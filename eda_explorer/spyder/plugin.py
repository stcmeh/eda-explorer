# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2025, Spyder Bot
#
# Licensed under the terms of the Not open source
# ----------------------------------------------------------------------------
"""
EDA Explorer Plugin.
"""

# Third-party imports
from qtpy.QtGui import QIcon

# Spyder imports
from spyder.api.plugins import Plugins, SpyderDockablePlugin
from spyder.api.translations import get_translation

# Local imports
from eda_explorer.spyder.confpage import EDAExplorerConfigPage
from eda_explorer.spyder.widgets import EDAExplorerWidget

_ = get_translation("eda_explorer.spyder")


class EDAExplorer(SpyderDockablePlugin):
    """
    EDA Explorer plugin.
    """

    NAME = "eda_explorer"
    REQUIRES = []
    OPTIONAL = []
    WIDGET_CLASS = EDAExplorerWidget
    CONF_SECTION = NAME
    CONF_WIDGET_CLASS = EDAExplorerConfigPage

    # --- Signals

    # --- SpyderDockablePlugin API
    # ------------------------------------------------------------------------
    def get_name(self):
        return _("EDA Explorer")

    def get_description(self):
        return _("EDA Explorer Spyder Widget")

    def get_icon(self):
        return QIcon()

    def on_initialize(self):
        widget = self.get_widget()
        

    def check_compatibility(self):
        valid = True
        message = ""  # Note: Remember to use _("") to localize the string
        return valid, message

    def on_close(self, cancellable=True):
        return True

    # --- Public API
    # ------------------------------------------------------------------------
