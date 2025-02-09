import os
from discord_bot_libs.constants import RunningEnvironment


running_mode = os.getenv('MODE', RunningEnvironment.TESTING)

if running_mode == RunningEnvironment.TESTING:
	from deploy_config.test_config import *
elif running_mode == RunningEnvironment.DEPLOY:
	from deploy_config.deploy_config import *