import pytest


@pytest.mark.script_launch_mode('subprocess')
def test_cli_rest_server(script_runner):
    """
    Needs to be done in subprocess due to monkey-patching
    """
    ret = script_runner.run('xbox-rest-server', '--help')
    assert ret.success


def test_cli_maincli(script_runner):
    ret = script_runner.run('xbox-cli', '--help')
    assert ret.success


def test_cli_discover(script_runner):
    ret = script_runner.run('xbox-discover', '--help')
    assert ret.success


def test_cli_poweron(script_runner):
    ret = script_runner.run('xbox-poweron', '--help')
    assert ret.success


def test_cli_poweroff(script_runner):
    ret = script_runner.run('xbox-poweroff', '--help')
    assert ret.success


def test_cli_repl(script_runner):
    ret = script_runner.run('xbox-repl', '--help')
    assert ret.success


def test_cli_replserver(script_runner):
    ret = script_runner.run('xbox-replserver', '--help')
    assert ret.success


def test_cli_textinput(script_runner):
    ret = script_runner.run('xbox-textinput', '--help')
    assert ret.success


def test_cli_gamepadinput(script_runner):
    ret = script_runner.run('xbox-gamepadinput', '--help')
    assert ret.success


def test_cli_tui(script_runner):
    ret = script_runner.run('xbox-tui', '--help')
    assert ret.success


def test_cli_falloutrelay(script_runner):
    ret = script_runner.run('xbox-fo4-relay', '--help')
    assert ret.success


def test_cli_pcap(script_runner):
    ret = script_runner.run('xbox-pcap', '--help')
    assert ret.success


def test_cli_recrypt(script_runner):
    ret = script_runner.run('xbox-recrypt', '--help')
    assert ret.success
