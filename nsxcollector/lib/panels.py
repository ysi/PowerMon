#!/opt/homebrew/bin/python3
from lib import tools


def simplePanel(panel_title, panel_type, infra, dashboard, grafana):
    # Panel
    panel = dashboard.panel(panel_title, panel_type)
    panel_parameters = {
        "name": panel_title,
        "type": panel_type,
        "datasource_uid": grafana.datasource_uid,
        "datasource_bucket": grafana.datasource_bucket,
        "node_ip": infra.cluster.members[0].ip_mgmt,
    } 
    panel.json_file = tools.renderPanel(panel_title, panel_parameters)
    dashboard.addPanel(panel)
    return dashboard