#!/usr/bin/env python2.7

class ZTPError(Exception):
  pass


class ZTPClientNotFoundError(ZTPError):
  pass


class ZTPMalformedClientRecordException(ZTPError):
  pass


class ZTPRenderingError(ZTPError):
  pass
