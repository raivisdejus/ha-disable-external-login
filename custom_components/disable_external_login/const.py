"""Constants for the Disable External Login integration."""

DOMAIN = "disable_external_login"

CONF_ENABLED = "enabled"
CONF_LOCAL_NETWORKS = "local_networks"

DEFAULT_LOCAL_NETWORKS = [
    "127.0.0.0/8",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "::1/128",
    "fd00::/8",
    "fe80::/10",
]
