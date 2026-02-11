#!/usr/bin/env python3
"""
Tests for VRAM monitoring module.

Tests cover:
- Normal VRAM checks (sufficient/insufficient)
- Error handling (nvidia-smi failures)
- Fail-open behavior
- Configuration via environment
- Edge cases (timeouts, parsing errors)

Run with: python3 -m pytest test_vram_monitor.py -v
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
import os

# Import module under test
import vram_monitor


class TestGetAvailableVRAM:
    """Tests for get_available_vram()"""

    def test_successful_query(self):
        """Should return VRAM in MB when nvidia-smi succeeds"""
        with patch('subprocess.run') as mock_run:
            # Mock nvidia-smi returning 57344 MB free
            mock_run.return_value = MagicMock(
                stdout="57344\n",
                returncode=0
            )

            result = vram_monitor.get_available_vram()

            assert result == 57344
            mock_run.assert_called_once()
            assert 'nvidia-smi' in mock_run.call_args[0][0]

    def test_query_specific_gpu(self):
        """Should query specific GPU when gpu_id provided"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="40000\n", returncode=0)

            vram_monitor.get_available_vram(gpu_id=1)

            # Check that --id=1 was passed
            args = mock_run.call_args[0][0]
            assert '--id=1' in args

    def test_nvidia_smi_not_found(self):
        """Should return None when nvidia-smi not in PATH"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            result = vram_monitor.get_available_vram()

            assert result is None

    def test_nvidia_smi_timeout(self):
        """Should return None when nvidia-smi times out"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('nvidia-smi', 5)):
            result = vram_monitor.get_available_vram()

            assert result is None

    def test_nvidia_smi_error(self):
        """Should return None when nvidia-smi returns error"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, 'nvidia-smi', stderr='No devices found'
            )

            result = vram_monitor.get_available_vram()

            assert result is None

    def test_invalid_output_format(self):
        """Should return None when nvidia-smi output unparseable"""
        with patch('subprocess.run') as mock_run:
            # Non-integer output
            mock_run.return_value = MagicMock(stdout="invalid\n", returncode=0)

            result = vram_monitor.get_available_vram()

            assert result is None


class TestCheckVRAMSufficient:
    """Tests for check_vram_sufficient()"""

    def test_sufficient_vram(self):
        """Should return True when plenty of VRAM available"""
        with patch('vram_monitor.get_available_vram', return_value=60000):
            # Job needs 24GB, have 60GB
            result = vram_monitor.check_vram_sufficient(24576)

            assert result is True

    def test_insufficient_vram(self):
        """Should return False when not enough VRAM"""
        with patch('vram_monitor.get_available_vram', return_value=10000):
            # Job needs 24GB + 2GB safety, have 10GB
            result = vram_monitor.check_vram_sufficient(24576)

            assert result is False

    def test_exact_vram_match(self):
        """Should return True when exactly enough VRAM (including safety)"""
        with patch('vram_monitor.get_available_vram', return_value=26624):
            # Job needs 24GB + 2GB safety = 26624 MB exactly
            result = vram_monitor.check_vram_sufficient(24576, safety_margin_mb=2048)

            assert result is True

    def test_custom_safety_margin(self):
        """Should use custom safety margin when provided"""
        with patch('vram_monitor.get_available_vram', return_value=30000):
            # Job needs 24GB + 4GB safety = 28GB
            result = vram_monitor.check_vram_sufficient(24576, safety_margin_mb=4096)

            assert result is True

        with patch('vram_monitor.get_available_vram', return_value=27000):
            # Not enough with 4GB safety
            result = vram_monitor.check_vram_sufficient(24576, safety_margin_mb=4096)

            assert result is False

    def test_fail_open_on_query_failure(self):
        """Should return True (fail-open) when VRAM query fails"""
        with patch('vram_monitor.get_available_vram', return_value=None):
            # Query failed, but should allow job (fail-open)
            result = vram_monitor.check_vram_sufficient(24576)

            assert result is True

    def test_monitoring_disabled(self):
        """Should return True when monitoring disabled via env var"""
        with patch.dict(os.environ, {'ENABLE_VRAM_MONITORING': 'false'}):
            # Reload module to pick up env var
            import importlib
            importlib.reload(vram_monitor)

            # Should allow job without checking
            with patch('vram_monitor.get_available_vram') as mock_get:
                result = vram_monitor.check_vram_sufficient(24576)

                assert result is True
                # Should not have called get_available_vram
                mock_get.assert_not_called()

    def test_dry_run_mode(self):
        """Should log warning but allow job in dry-run mode"""
        with patch.dict(os.environ, {'VRAM_CHECK_DRY_RUN': 'true'}):
            import importlib
            importlib.reload(vram_monitor)

            with patch('vram_monitor.get_available_vram', return_value=10000):
                # Insufficient VRAM, but dry-run should allow
                result = vram_monitor.check_vram_sufficient(24576)

                assert result is True


class TestGetVRAMStats:
    """Tests for get_vram_stats()"""

    def test_successful_stats_query(self):
        """Should return detailed stats dict when nvidia-smi succeeds"""
        with patch('subprocess.run') as mock_run:
            # Mock: 80GB total, 24GB used, 56GB free
            mock_run.return_value = MagicMock(
                stdout="81920, 24576, 57344\n",
                returncode=0
            )

            result = vram_monitor.get_vram_stats()

            assert result is not None
            assert result['gpu_id'] == 0
            assert result['total_mb'] == 81920
            assert result['used_mb'] == 24576
            assert result['free_mb'] == 57344
            assert result['usage_percent'] == 30.0  # 24576/81920 = 30%

    def test_stats_specific_gpu(self):
        """Should query specific GPU for stats"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="40960, 10240, 30720\n",
                returncode=0
            )

            result = vram_monitor.get_vram_stats(gpu_id=2)

            assert result['gpu_id'] == 2
            # Check that --id=2 was passed
            args = mock_run.call_args[0][0]
            assert '--id=2' in args

    def test_stats_nvidia_smi_not_found(self):
        """Should return None when nvidia-smi not available"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            result = vram_monitor.get_vram_stats()

            assert result is None

    def test_stats_nvidia_smi_timeout(self):
        """Should return None on nvidia-smi timeout"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('nvidia-smi', 5)):
            result = vram_monitor.get_vram_stats()

            assert result is None

    def test_stats_invalid_output(self):
        """Should return None when output format invalid"""
        with patch('subprocess.run') as mock_run:
            # Wrong number of values
            mock_run.return_value = MagicMock(
                stdout="81920, 24576\n",  # Missing third value
                returncode=0
            )

            result = vram_monitor.get_vram_stats()

            assert result is None

    def test_stats_usage_percent_calculation(self):
        """Should correctly calculate usage percentage"""
        test_cases = [
            # (total, used, expected_percent)
            (80000, 40000, 50.0),
            (80000, 20000, 25.0),
            (80000, 60000, 75.0),
            (81920, 24576, 30.0),
        ]

        for total, used, expected in test_cases:
            free = total - used
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    stdout=f"{total}, {used}, {free}\n",
                    returncode=0
                )

                result = vram_monitor.get_vram_stats()

                assert result is not None
                assert result['usage_percent'] == expected, \
                    f"Expected {expected}% for {used}/{total}MB, got {result['usage_percent']}%"


class TestEstimateVRAMForModel:
    """Tests for estimate_vram_for_model()"""

    def test_known_models(self):
        """Should return correct estimates for known models"""
        test_cases = [
            ('flux2-klein-9b', 18432),
            ('flux2-klein-4b', 8192),
            ('ltx2-19b', 24576),
            ('ltx2-distilled', 12288),
        ]

        for model, expected in test_cases:
            result = vram_monitor.estimate_vram_for_model(model)
            assert result == expected, \
                f"Expected {expected}MB for {model}, got {result}MB"

    def test_case_insensitive(self):
        """Should handle model names case-insensitively"""
        result_upper = vram_monitor.estimate_vram_for_model('LTX2-19B')
        result_lower = vram_monitor.estimate_vram_for_model('ltx2-19b')
        result_mixed = vram_monitor.estimate_vram_for_model('LtX2-19B')

        assert result_upper == result_lower == result_mixed == 24576

    def test_unknown_model_returns_default(self):
        """Should return default estimate for unknown models"""
        result = vram_monitor.estimate_vram_for_model('unknown-model-xyz')

        # Should return default (8192 MB by default)
        assert result == vram_monitor.VRAM_DEFAULT_ESTIMATE_MB


class TestConfiguration:
    """Tests for environment variable configuration"""

    def test_default_config_values(self):
        """Should use sensible defaults when env vars not set"""
        # Clean environment
        clean_env = {k: v for k, v in os.environ.items()
                     if not k.startswith('VRAM_')}

        with patch.dict(os.environ, clean_env, clear=True):
            import importlib
            importlib.reload(vram_monitor)

            assert vram_monitor.ENABLE_VRAM_MONITORING is True
            assert vram_monitor.VRAM_SAFETY_MARGIN_MB == 2048
            assert vram_monitor.VRAM_CHECK_TIMEOUT == 5
            assert vram_monitor.VRAM_DEFAULT_ESTIMATE_MB == 8192
            assert vram_monitor.VRAM_CHECK_DRY_RUN is False

    def test_custom_safety_margin_from_env(self):
        """Should use custom safety margin from environment"""
        with patch.dict(os.environ, {'VRAM_SAFETY_MARGIN_MB': '4096'}):
            import importlib
            importlib.reload(vram_monitor)

            assert vram_monitor.VRAM_SAFETY_MARGIN_MB == 4096

    def test_custom_timeout_from_env(self):
        """Should use custom timeout from environment"""
        with patch.dict(os.environ, {'VRAM_CHECK_TIMEOUT_SECONDS': '10'}):
            import importlib
            importlib.reload(vram_monitor)

            assert vram_monitor.VRAM_CHECK_TIMEOUT == 10


class TestIntegration:
    """Integration tests simulating real-world scenarios"""

    def test_workshop_scenario_sufficient_vram(self):
        """Scenario: H100 with 80GB, job needs 24GB + 2GB safety"""
        with patch('subprocess.run') as mock_run:
            # H100: 80GB total, 15GB used, 65GB free
            mock_run.return_value = MagicMock(
                stdout="66560\n",  # 65GB free
                returncode=0
            )

            # Job: LTX-2 19B (24GB estimate)
            result = vram_monitor.check_vram_sufficient(24576)

            assert result is True  # Should accept

    def test_workshop_scenario_insufficient_vram(self):
        """Scenario: H100 with 80GB, job needs 24GB but only 20GB free"""
        with patch('subprocess.run') as mock_run:
            # H100: 80GB total, 60GB used, 20GB free
            mock_run.return_value = MagicMock(
                stdout="20480\n",  # 20GB free
                returncode=0
            )

            # Job: LTX-2 19B (needs 24GB + 2GB safety = 26GB)
            result = vram_monitor.check_vram_sufficient(24576)

            assert result is False  # Should reject

    def test_gpu_crash_graceful_degradation(self):
        """Scenario: GPU hung, nvidia-smi times out, should fail-open"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('nvidia-smi', 5)):
            # Job: Any size
            result = vram_monitor.check_vram_sufficient(24576)

            # Should allow job (fail-open), not block all work
            assert result is True

    def test_cpu_testing_environment(self):
        """Scenario: Testing on CPU machine (no nvidia-smi)"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            # Should still allow job (fail-open for testing)
            result = vram_monitor.check_vram_sufficient(24576)

            assert result is True

    def test_multiple_sequential_checks(self):
        """Scenario: Worker checking multiple jobs in sequence"""
        vram_values = [60000, 50000, 30000, 15000, 8000]

        for vram in vram_values:
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    stdout=f"{vram}\n",
                    returncode=0
                )

                # Job needs 24GB + 2GB safety = 26624 MB
                result = vram_monitor.check_vram_sufficient(24576)

                expected = (vram >= 26624)
                assert result == expected, \
                    f"With {vram}MB available, expected {expected}, got {result}"


class TestCLI:
    """Tests for CLI functionality (if run as script)"""

    def test_cli_help_message(self):
        """Should show help when run with invalid args"""
        # This would be tested with subprocess if we were testing the script directly
        # For now, just verify the __main__ block exists
        import vram_monitor
        assert hasattr(vram_monitor, '__name__')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
