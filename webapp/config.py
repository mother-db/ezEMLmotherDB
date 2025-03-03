#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: config

:Synopsis:

:Author:
    servilla

:Created:
    3/6/18
"""


class Config(object):

    # Flask app configuration
    SECRET_KEY = "SECRET KEY"
    DEBUG = True
    FLASH_DEBUG = False
    LOG_DEBUG = False

    PASTA_URL = "https://pasta.lternet.edu/package"

    #AUTH = "https://auth.edirepository.org/auth"
    AUTH = "https://localhost:5000/eml/auth"
    #TARGET = "ezeml.edirepository.org"
    TARGET = "localhost:5000/eml"

    DOMAINS = {
        "edi": "o=EDI,dc=edirepository,dc=org",
    }

    ACTIVE_PACKAGE = "active.pkl"

    AUTH_SYSTEM_ATTRIBUTE_VALUE = (
        "https://pasta.edirepository.org/authentication"
    )
    ORDER_ATTRIBUTE_VALUE = "allowFirst"
    SCOPE_ATTRIBUTE_VALUE = "document"
#PT5/27    SYSTEM_ATTRIBUTE_VALUE = "https://pasta.edirepository.org"
    SYSTEM_ATTRIBUTE_VALUE = "mother-db.org"    #PT5/27

    # Email configuration
    HOVER_MAIL = "MAIL_USER"
    HOVER_PASSWORD = "MAIL_PASSWORD"
