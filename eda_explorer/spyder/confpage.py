# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright © 2025, Spyder Bot
#
# Licensed under the terms of the Not open source
# ----------------------------------------------------------------------------
"""
EDA Explorer Preferences Page.
"""
from spyder.api.preferences import PluginConfigPage
from spyder.api.translations import get_translation

_ = get_translation("eda_explorer.spyder")


class EDAExplorerConfigPage(PluginConfigPage):

    # --- PluginConfigPage API
    # ------------------------------------------------------------------------
    def setup_page(self):
        pass
