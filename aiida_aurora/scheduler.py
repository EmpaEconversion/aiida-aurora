"""
Plugin for the Tomato scheduler.
"""
import datetime
import re

import yaml

from aiida.common import exceptions
from aiida.common.escaping import escape_for_bash
from aiida.common.extendeddicts import AttributeDict
from aiida.schedulers import Scheduler, SchedulerError
from aiida.schedulers.datastructures import JobInfo, JobResource, JobState

# There is no "job owner" in tomato.

# Mapping of Tomato states to AiiDA `JobState`s
#
# The following statuses are defined in tomato:
#  - q   job is queued. Jobs shouldn't stay in q too long as that indicates there
#        is no pipeline that can process the payload.
#  - qw  job is queued and a matching pipeline has been found, but it is either busy,
#        not ready, or without the correct sample
#  - r   job is running
#  - c   job has completed successfully
#  - ce  job has completed with an error - output data not guaranteed, might be present in the job folder.
#  - cd  job has been cancelled - output data should be available as specified in the yamlfile

_MAP_STATUS_TOMATO = {
    "q": JobState.QUEUED,  # JobState.QUEUED_HELD ?
    "qw": JobState.QUEUED,
    "r": JobState.RUNNING,
    "c": JobState.DONE,
    "ce": JobState.DONE,
    "cd": JobState.DONE,
}

_MAP_ANNOTATION_TOMATO = {
    "q": "Queued",
    "qw": "Queued, matching pipeline found",
    "r": "Running",
    "c": "Completed successfully",
    "ce": "Completed with error",
    "cd": "Cancelled",
}


class TomatoResource(JobResource):
    """Class for Tomato job resources."""

    @classmethod
    def validate_resources(cls, **kwargs):
        """Validate the resources against the job resource class of this scheduler.

        :param kwargs: dictionary of values to define the job resources
        :raises ValueError: if the resources are invalid or incomplete
        :return: optional tuple of parsed resource settings
        """
        resources = AttributeDict()
        # *Essentially ignore all job resources!*
        return resources

    def __init__(self, **kwargs):
        """Initialize the job resources from the passed arguments.

        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = self.validate_resources(**kwargs)
        super().__init__(resources)

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls):
        """Return True if this subclass accepts a `default_mpiprocs_per_machine` key, False otherwise."""
        return False

    def get_tot_num_mpiprocs(self):
        """Return the total number of cpus of this job resource."""
        return 1


class TomatoScheduler(Scheduler):
    """
    Support for the Tomato scheduler (https://github.com/dgbowl/tomato)
    Supports tomato version 0.2a1
    """

    _logger = Scheduler._logger.getChild("tomato")

    # Query only by list of jobs and not by user
    _features = {
        "can_query_by_user": False,
    }

    # The class to be used for the job resource.
    _job_resource_class = TomatoResource

    _map_status = _MAP_STATUS_TOMATO

    # the command used to submit the script
    _shell_cmd = ""

    # the scheduler command
    # (NOTE: if applicable, you should configure the computer to load the appropriate virtual environment,
    # in order to make this command available)
    KETCHUP = "ketchup"

    def _get_joblist_command(self, jobs=None, user=None):
        """The command to report full information on existing jobs.

        :return: a string of the command to be executed to determine the active jobs.
        """

        if user:
            raise exceptions.FeatureNotAvailable("Cannot query by user")

        if jobs:
            if isinstance(jobs, str):
                command = f"{self.KETCHUP} status {escape_for_bash(jobs)}"
            else:
                command = f"{self.KETCHUP} status "
                try:
                    command += " ".join(f"{j}" for j in jobs)
                except TypeError as e:
                    raise TypeError(
                        "If provided, the 'jobs' variable must be a string or an iterable of strings"
                    ) from e
        else:
            command = f"{self.KETCHUP} status queue -v"

        self._logger.debug(f"ketchup command: {command}")
        return command

    def _get_detailed_job_info_command(self, job_id):
        """Return the command to run to get the detailed information on a job,
        even after the job has finished.

        The output text is just retrieved, and returned for logging purposes.
        """
        return f"{self.KETCHUP} status {escape_for_bash(job_id)}"

    def _get_submit_script_header(self, job_tmpl):
        """Return the submit script final part, using the parameters from the job template.

        :param job_tmpl: a ``JobTemplate`` instance with relevant parameters set.
        """
        # set the `_shell_cmd` class attribute from the job template
        # FIXME shell_type used to be job_tmpl.shell_type, which was added to
        # aiida-core's `JobTemplate` class by Loris. Awaiting resolution.
        shell_type = "powershell"
        # shell_type = "bash"  # uncomment when debugging on Linux
        TomatoScheduler._shell_cmd = shell_type
        self._logger.debug(f"_get_submit_script_header: _shell_cmd: {self._shell_cmd}")

        import string

        if job_tmpl.job_name:
            # I leave only letters, numbers, dots, dashes and underscores
            # Note: I don't compile the regexp, I am going to use it only once
            job_title = re.sub(r"[^a-zA-Z0-9_.-]+", "", job_tmpl.job_name)

            # prepend a 'j' (for 'job') before the string if the string
            # is now empty or does not start with a valid character
            if not job_title or (job_title[0] not in string.ascii_letters + string.digits):
                job_title = f"j{job_title}"

            # Truncate to the first 128 characters
            # Nothing is done if the string is shorter.
            job_title = job_title[:128]
            if shell_type == "powershell":
                header = f"$JOB_TITLE='{job_title}'"
            else:
                header = f"JOB_TITLE='{job_title}'"
        else:
            header = ""

        return header

    def _get_submit_command(self, submit_script):
        """Return the string to execute to submit a given script.

        .. warning:: the `submit_script` should already have been bash-escaped

        :param submit_script: the path of the submit script relative to the working directory.
        :return: the string to execute to submit a given script.
        """
        # Similarly to the 'direct' scheduler, we submit a bash script that actually executes
        # `ketchup submit {payload}`
        # the output of it is parsed *immediately* by _parse_submit_output
        submit_command = f"{self._shell_cmd} {submit_script}"

        self._logger.info(f"submitting with: {submit_command}")

        return submit_command

    def _get_run_line(self, codes_info, codes_run_mode):
        """Return a string with the line to execute a specific code with specific arguments.

        :parameter codes_info: a list of `aiida.common.datastructures.CodeInfo` objects. Each contains the information
            needed to run the code. I.e. `cmdline_params`, `stdin_name`, `stdout_name`, `stderr_name`, `join_files`. See
            the documentation of `JobTemplate` and `CodeInfo`.
        :parameter codes_run_mode: instance of `aiida.common.datastructures.CodeRunMode` contains the information on how
            to launch the multiple codes.
        :return: string with format: [executable] [args] {[ < stdin ]} {[ < stdout ]} {[2>&1 | 2> stderr]}

        Tomato: the only customization with respect to the base-class `_get_run_line` method consists in not using
        `escape_for_bash`, because we want to make use of environmental variables in the run line.
        """
        from aiida.common.datastructures import CodeRunMode

        list_of_runlines = []

        for code_info in codes_info:
            command_to_exec_list = []
            for arg in code_info.cmdline_params:
                command_to_exec_list.append(arg)
                # command_to_exec_list.append(escape_for_bash(arg))
            command_to_exec = " ".join(command_to_exec_list)

            stdin_str = (f"< {escape_for_bash(code_info.stdin_name)}" if code_info.stdin_name else "")
            stdout_str = (f"> {escape_for_bash(code_info.stdout_name)}" if code_info.stdout_name else "")

            join_files = code_info.join_files
            if join_files:
                stderr_str = "2>&1"
            else:
                stderr_str = (f"2> {escape_for_bash(code_info.stderr_name)}" if code_info.stderr_name else "")

            output_string = f"{command_to_exec} {stdin_str} {stdout_str} {stderr_str}"

            list_of_runlines.append(output_string)

        self.logger.debug(f"_get_run_line output: {list_of_runlines}")

        if codes_run_mode == CodeRunMode.PARALLEL:
            list_of_runlines.append("wait\n")
            return " &\n\n".join(list_of_runlines)

        if codes_run_mode == CodeRunMode.SERIAL:
            return "\n\n".join(list_of_runlines)

        raise NotImplementedError("Unrecognized code run mode")

    def _parse_joblist_output(self, retval, stdout, stderr):
        """Parse the joblist output as returned by executing the command returned by `_get_joblist_command` method.

        :return: list of `JobInfo` objects, one of each job each with at least its default params implemented.
        """
        if retval != 0:
            raise SchedulerError(
                f"""ketchup returned exit code {retval} (_parse_joblist_output function)"""
                f"""stdout='{stdout.strip()}'"""
                f"""stderr='{stderr.strip()}'"""
            )
        if stderr.strip():
            self.logger.warning(
                f"ketchup returned exit code 0 (_parse_joblist_output function) but non-empty stderr='{stderr.strip()}'"
            )

        # remove all empty lines and lines containing 'ERROR'
        jobdata_raw = "\n".join(l for l in stdout.splitlines() if l and "ERROR" not in l)

        def convert_datetime(dt):
            if isinstance(dt, datetime.datetime):
                return dt
            try:
                return datetime.datetime.fromisoformat(dt)
            except Exception:
                return None

        # Create dictionary and parse specific fields
        job_list = []

        if "===========================" in jobdata_raw:
            # the command was 'ketchup status queue'
            jobdata_raw = jobdata_raw.splitlines()
            if len(jobdata_raw) > 2:
                for line in jobdata_raw[2:]:
                    job = line.split()
                    this_job = JobInfo()
                    this_job.job_id = job[0]
                    this_job.title = job[1]

                    try:
                        this_job.job_state = _MAP_STATUS_TOMATO[job[2]]
                        this_job.annotation = _MAP_ANNOTATION_TOMATO[job[2]]
                    except KeyError:
                        self.logger.warning(f"Unrecognized job_state '{job[2]}' for job id {this_job.job_id}")
                        this_job.job_state = JobState.UNDETERMINED

                    if len(job) == 3:
                        this_job.pipeline = None
                    elif len(job) == 4:
                        this_job.pipeline = job[3]
                    else:
                        raise ValueError(f"More than 4 columns returned by ketchup status queue\n{job}")

                    # Everything goes here anyway for debugging purposes
                    this_job.raw_data = job

                    # I append to the list of jobs to return
                    job_list.append(this_job)
            else:
                pass  # there are no jobs in the queue

        else:
            # the command was 'ketchup status {jobid} ...'
            # the output is yaml-formatted
            jobdata_parsed = yaml.full_load(jobdata_raw)

            for this_job_dict in jobdata_parsed:
                this_job = JobInfo()
                this_job.job_id = str(this_job_dict["jobid"])
                this_job.title = this_job_dict["jobname"]
                try:
                    this_job_status = this_job_dict["status"]
                    this_job.job_state = _MAP_STATUS_TOMATO[this_job_status]
                    this_job.annotation = _MAP_ANNOTATION_TOMATO[this_job_status]
                except KeyError:
                    self.logger.warning(f"Unrecognized job_state '{this_job_status}' for job id {this_job.job_id}")
                    this_job.job_state = JobState.UNDETERMINED

                # yaml parses iso-format datetime strings automatically:
                this_job.submission_time = convert_datetime(this_job_dict.get("submitted"))
                this_job.dispatch_time = convert_datetime(this_job_dict.get("executed"))
                this_job.finish_time = convert_datetime(this_job_dict.get("completed"))
                this_job.allocated_machines = this_job_dict.get("pipeline")
                # ignored: this_job_dict.get("pid")

                job_list.append(this_job)  # append last job

        return job_list

    def _parse_submit_output(self, retval, stdout, stderr):
        """Parse the output of the submit command returned by calling the `_get_submit_command` command.

        :return: a string with the job ID.
        """
        if retval != 0:
            self._logger.error(f"Error in _parse_submit_output: retval={retval}; stdout={stdout}; stderr={stderr}")
            raise SchedulerError(f"Error during submission, retval={retval}; stdout={stdout}; stderr={stderr}")

        if stderr.strip():
            self._logger.warning(f"in _parse_submit_output there was some text in stderr: {stderr}")

        # I check for the jobid in the output
        stdout_dict = yaml.full_load(stdout)
        if "jobid" in stdout_dict:
            self._logger.debug(f"The submitted jobid is {stdout_dict['jobid']}")
            # HACK did not need to str-cast prior to aiida 2.x upgrade
            return str(stdout_dict["jobid"])

        # If I am here, no jobid was found
        self.logger.error(f"in _parse_submit_output: unable to find the job id: {stdout}")
        raise SchedulerError(
            "Error during submission, could not retrieve the jobID from ketchup output; see log for more info."
        )

    def _get_kill_command(self, jobid):
        """Return the command to kill the job with specified jobid."""

        kill_command = f"{self.KETCHUP} cancel {jobid}"

        self._logger.info(f"killing job {jobid}: {kill_command}")

        return kill_command

    def _parse_kill_output(self, retval, stdout, stderr):
        """Parse the output of the kill command.

        :return: True if everything seems ok, False otherwise.
        """
        if retval != 0:
            self._logger.error(f"Error in _parse_kill_output: retval={retval}; stdout={stdout}; stderr={stderr}")
            return False

        if stderr.strip():
            self._logger.warning(f"in _parse_kill_output there was some text in stderr: {stderr}")

        if stdout.strip():
            self._logger.warning(f"in _parse_kill_output there was some text in stdout: {stdout}")

        return True

    def parse_output(self, detailed_job_info, stdout, stderr):
        """Parse the output of the scheduler.

        :param detailed_job_info: dictionary with the output returned by the `Scheduler.get_detailed_job_info` command.
            This should contain the keys `retval`, `stdout` and `stderr` corresponding to the return value, stdout and
            stderr returned by the accounting command executed for a specific job id.
        :param stdout: string with the output written by the scheduler to stdout
        :param stderr: string with the output written by the scheduler to stderr
        :return: None or an instance of `aiida.engine.processes.exit_code.ExitCode`
        :raises TypeError or ValueError: if the passed arguments have incorrect type or value
        """
        raise NotImplementedError()
