from core import config

fc = config.Function()

print(fc.get_config_value('theme'))
print(fc.get_config_value('theme.primary'))

print(fc.get_config_value('system.locale'))