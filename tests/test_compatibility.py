import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    'hy2hop_compatibility', Path(__file__).resolve().parent.parent / 'hy2hop.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        for target, name, value in (
            (m.os, 'geteuid', 0),
            (m.Path, 'exists', True),
            (m.shutil, 'which', '/usr/bin/command'),
        ):
            mock = patch.object(target, name, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        # Prerequisite detection must never change firewall/system state.
        mock = patch.object(m, 'run')
        self.run = mock.start()
        self.addCleanup(mock.stop)

    def check_release(self, text):
        with patch.object(m.Path, 'read_text', return_value=text):
            m.prerequisites()
        self.run.assert_not_called()

    def test_supported_ubuntu_releases(self):
        for version in ('20.04', '20.04.6', '22.04', '24.04', '24.10', '26.04'):
            with self.subTest(version=version):
                self.check_release('ID=ubuntu\nVERSION_ID="' + version + '"\n')

    def test_ubuntu_22045_uses_series_version_id(self):
        self.check_release(
            'PRETTY_NAME="Ubuntu 22.04.5 LTS"\nNAME="Ubuntu"\n'
            'VERSION_ID="22.04"\nVERSION="22.04.5 LTS (Jammy Jellyfish)"\n'
            'ID=ubuntu\nID_LIKE=debian\n')

    def test_quoted_id_and_point_version(self):
        self.check_release('ID="ubuntu"\nVERSION_ID="22.04.5"\n')
        self.check_release("ID='ubuntu'\nVERSION_ID='22.04'\n")
        self.check_release('ID=ubuntu\nVERSION_ID=22.04\n')

    def test_unsupported_or_invalid_version_rejected(self):
        for version in ('18.04', '19.10', '20.01', '', '22', '22.04garbage', 'rolling'):
            with self.subTest(version=version):
                with self.assertRaisesRegex(RuntimeError, '需要 Ubuntu'):
                    self.check_release('ID=ubuntu\nVERSION_ID="' + version + '"\n')

    def test_other_distributions_and_missing_id_rejected(self):
        for ident in ('debian', 'linuxmint', ''):
            with self.subTest(ident=ident):
                with self.assertRaisesRegex(RuntimeError, '需要 Ubuntu'):
                    self.check_release('ID=' + ident + '\nID_LIKE=ubuntu\nVERSION_ID="22.04"\n')

    def test_missing_version_rejected(self):
        with self.assertRaisesRegex(RuntimeError, '需要 Ubuntu'):
            self.check_release('ID=ubuntu\n')

    def test_python_38_and_310_accepted(self):
        for version in ((3, 8), (3, 10), (3, 12)):
            with self.subTest(version=version), patch.object(m.sys, 'version_info', version):
                self.check_release('ID=ubuntu\nVERSION_ID="22.04"\n')

    def test_old_python_rejected(self):
        with patch.object(m.sys, 'version_info', (3, 7)):
            with self.assertRaisesRegex(RuntimeError, 'Python 3.8'):
                self.check_release('ID=ubuntu\nVERSION_ID="22.04"\n')

    def test_root_still_required(self):
        with patch.object(m.os, 'geteuid', return_value=1000):
            with self.assertRaisesRegex(RuntimeError, 'root'):
                m.prerequisites()

    def test_systemd_still_required(self):
        with patch.object(m.Path, 'exists', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'systemd'):
                m.prerequisites()

    def test_missing_commands_still_rejected(self):
        for missing in ('systemctl', 'ss', 'ip', 'apt-get'):
            with self.subTest(command=missing), patch.object(
                    m.shutil, 'which', side_effect=lambda cmd: None if cmd == missing else '/usr/bin/' + cmd):
                with self.assertRaisesRegex(RuntimeError, '缺少系统命令 ' + missing):
                    self.check_release('ID=ubuntu\nVERSION_ID="22.04"\n')


if __name__ == '__main__':
    unittest.main()
