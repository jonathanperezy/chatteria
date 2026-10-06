from . import controllers, models

def pre_init_hooks(env):
    """ Pre init hooks """
    # Try install python dependences on install
    import subprocess
    subprocess.run(["pip", "install", 'google-genai', '--break-system-packages'])


