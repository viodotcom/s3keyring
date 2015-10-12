#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Command line interface"""

from __future__ import print_function

import click


@click.group(name='s3keyring')
def main():
    """S3 backend for Python's keyring module
    """
    pass


if __name__ == '__main__':
    main()
