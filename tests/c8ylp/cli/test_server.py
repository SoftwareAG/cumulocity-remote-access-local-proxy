"""Server ssh tests"""

import pytest
import responses
from click.testing import CliRunner
from c8ylp.main import cli
from tests.env import Environment
from tests.fixtures import FixtureCumulocityAPI


@pytest.mark.skip
def test_server_mode(c8yserver: FixtureCumulocityAPI, env: Environment):
    """Execute command via ssh then exit"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        c8yserver.simulate_pre_authenticated(serial)

        # with subprocess.Popen(["python3", "-m", "server", ])
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["server", serial],
            env=env.create_authenticated(),
        )

        assert result.exit_code == 0
        assert result.stdout

    run()
