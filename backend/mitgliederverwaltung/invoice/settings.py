#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from reportlab.lib.units import cm


IBAN_CREDITOR = "Ö.Ges.f.Vermessung u.Geoinformation 1025 Wien"
BANK = "BAWAG-P.S.K"
BIC = "BAWAATWW"
IBAN_NUMBER = "AT216000000001190933"
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = "templates"
OUT_DIR = "out"
ISO_DATE = "%Y-%m-%d"

LOGO_WIDTH = 13.*cm
LOGO_HEIGHT = 2.334*cm

A4_HEIGHT = 29.7*cm
A4_WIDTH = 21.0*cm

OVG_NAME = "Österr. Zeitschrift für Vermessung und Geoinformation"
OVG_TREASURER = "Wolfgang Gold, Schatzmeister"
OVG_SITE = "www.ovg.at"
OVG_ZVR = "403011926"
