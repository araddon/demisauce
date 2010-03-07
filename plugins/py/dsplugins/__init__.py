import logging


def echo(job):
    print(job.arg)
    return job.arg