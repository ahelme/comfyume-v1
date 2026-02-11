#!/usr/bin/env python3
"""
VRAM monitoring for ComfyUI worker jobs.

Provides VRAM checking to prevent OOM crashes on GPU workers.
Uses nvidia-smi to query GPU memory state before accepting jobs.

Key features:
- Fail-open: If monitoring unavailable, allow job (don't block work)
- Configurable safety margin (default 2GB)
- Structured logging for debugging
- Simple subprocess-based implementation

Integration points:
- worker.py: Check VRAM before queueing jobs
- Health endpoints: Expose VRAM stats for monitoring
- Worker status: Report VRAM to queue manager

Author: Verda Team
Created: 2026-01-31
Issue: comfyume #4
"""

import os
import subprocess
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Configuration from environment
ENABLE_VRAM_MONITORING = os.getenv("ENABLE_VRAM_MONITORING", "true").lower() == "true"
VRAM_SAFETY_MARGIN_MB = int(os.getenv("VRAM_SAFETY_MARGIN_MB", "2048"))  # Default 2GB
VRAM_CHECK_TIMEOUT = int(os.getenv("VRAM_CHECK_TIMEOUT_SECONDS", "5"))  # nvidia-smi timeout
VRAM_DEFAULT_ESTIMATE_MB = int(os.getenv("VRAM_DEFAULT_ESTIMATE_MB", "8192"))  # 8GB fallback
VRAM_CHECK_DRY_RUN = os.getenv("VRAM_CHECK_DRY_RUN", "false").lower() == "true"


def get_available_vram(gpu_id: int = 0) -> Optional[int]:
    """
    Get available VRAM in MB using nvidia-smi.

    Args:
        gpu_id: GPU device ID (default 0 for first GPU)

    Returns:
        Available VRAM in MB, or None if query fails

    Example:
        >>> vram_mb = get_available_vram()
        >>> if vram_mb:
        ...     print(f"Available: {vram_mb}MB")

    Note:
        Returns None on any error (nvidia-smi not found, timeout, etc.)
        This allows fail-open behavior in check_vram_sufficient()
    """
    try:
        result = subprocess.run(
            [
                'nvidia-smi',
                '--query-gpu=memory.free',
                '--format=csv,noheader,nounits',
                f'--id={gpu_id}'
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=VRAM_CHECK_TIMEOUT
        )

        # Parse result (should be single integer)
        vram_mb = int(result.stdout.strip())
        logger.debug(f"GPU {gpu_id}: {vram_mb}MB VRAM available")
        return vram_mb

    except subprocess.TimeoutExpired:
        logger.error(
            f"nvidia-smi timed out after {VRAM_CHECK_TIMEOUT}s - "
            "GPU may be hung or overloaded"
        )
        return None

    except subprocess.CalledProcessError as e:
        logger.error(
            f"nvidia-smi failed with exit code {e.returncode}: {e.stderr}"
        )
        return None

    except FileNotFoundError:
        logger.error(
            "nvidia-smi not found - VRAM monitoring unavailable "
            "(GPU drivers not installed or not in PATH)"
        )
        return None

    except (ValueError, IndexError) as e:
        logger.error(
            f"Failed to parse nvidia-smi output '{result.stdout}': {e}"
        )
        return None

    except Exception as e:
        logger.error(f"Unexpected error querying VRAM: {e}")
        return None


def check_vram_sufficient(
    estimated_vram_mb: int,
    safety_margin_mb: Optional[int] = None,
    gpu_id: int = 0
) -> bool:
    """
    Check if sufficient VRAM available for job.

    Fail-open strategy: If monitoring is disabled or unavailable,
    allow the job (return True). This prevents blocking work when
    VRAM monitoring breaks.

    Args:
        estimated_vram_mb: Estimated VRAM needed for job (from metadata)
        safety_margin_mb: Extra VRAM buffer (default from env: 2GB)
        gpu_id: GPU device ID (default 0)

    Returns:
        True if sufficient VRAM or monitoring unavailable (fail-open)
        False only if monitoring confirms insufficient VRAM

    Example:
        >>> # Job needs 24GB, check before queueing
        >>> if check_vram_sufficient(24576):
        ...     queue_job()
        ... else:
        ...     reject_job("Insufficient GPU memory")

    Note:
        Logs all decisions for debugging. In dry-run mode, logs warning
        but always returns True (for testing without blocking).
    """
    # Use configured safety margin if not provided
    if safety_margin_mb is None:
        safety_margin_mb = VRAM_SAFETY_MARGIN_MB

    # If monitoring disabled, allow job
    if not ENABLE_VRAM_MONITORING:
        logger.debug(
            "VRAM monitoring disabled (ENABLE_VRAM_MONITORING=false), "
            f"allowing job requiring {estimated_vram_mb}MB"
        )
        return True

    # Query available VRAM
    available_mb = get_available_vram(gpu_id)

    # If query failed, fail-open (allow job)
    if available_mb is None:
        logger.warning(
            f"Could not check VRAM for job requiring {estimated_vram_mb}MB - "
            "allowing job (fail-open)"
        )
        return True

    # Calculate required VRAM (estimate + safety margin)
    required_mb = estimated_vram_mb + safety_margin_mb

    # Check if sufficient
    sufficient = available_mb >= required_mb

    if sufficient:
        logger.info(
            f"VRAM check PASSED: {available_mb}MB available >= "
            f"{required_mb}MB required ({estimated_vram_mb}MB + {safety_margin_mb}MB safety) "
            f"[GPU {gpu_id}]"
        )
    else:
        logger.warning(
            f"VRAM check FAILED: {available_mb}MB available < "
            f"{required_mb}MB required ({estimated_vram_mb}MB + {safety_margin_mb}MB safety) "
            f"[GPU {gpu_id}]"
        )

    # Dry-run mode: log but don't actually reject
    if VRAM_CHECK_DRY_RUN and not sufficient:
        logger.warning(
            "DRY RUN MODE: Would reject job, but allowing anyway "
            "(VRAM_CHECK_DRY_RUN=true)"
        )
        return True

    return sufficient


def get_vram_stats(gpu_id: int = 0) -> Optional[Dict[str, Any]]:
    """
    Get detailed VRAM statistics for monitoring dashboard.

    Args:
        gpu_id: GPU device ID (default 0)

    Returns:
        Dictionary with VRAM stats, or None if query fails:
        {
            'gpu_id': 0,
            'total_mb': 81920,
            'used_mb': 24576,
            'free_mb': 57344,
            'usage_percent': 30.0
        }

    Example:
        >>> stats = get_vram_stats()
        >>> if stats:
        ...     print(f"GPU {stats['usage_percent']}% full")

    Note:
        Used for health endpoints and worker status reporting.
        Returns None on any error (fail-safe).
    """
    try:
        result = subprocess.run(
            [
                'nvidia-smi',
                '--query-gpu=memory.total,memory.used,memory.free',
                '--format=csv,noheader,nounits',
                f'--id={gpu_id}'
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=VRAM_CHECK_TIMEOUT
        )

        # Parse result (format: "total,used,free")
        total_str, used_str, free_str = result.stdout.strip().split(',')
        total_mb = int(total_str.strip())
        used_mb = int(used_str.strip())
        free_mb = int(free_str.strip())

        # Calculate usage percentage
        usage_percent = round((used_mb / total_mb) * 100, 1) if total_mb > 0 else 0.0

        stats = {
            'gpu_id': gpu_id,
            'total_mb': total_mb,
            'used_mb': used_mb,
            'free_mb': free_mb,
            'usage_percent': usage_percent
        }

        logger.debug(
            f"GPU {gpu_id} stats: {used_mb}/{total_mb}MB ({usage_percent}%)"
        )

        return stats

    except subprocess.TimeoutExpired:
        logger.error(
            f"nvidia-smi timed out after {VRAM_CHECK_TIMEOUT}s getting stats"
        )
        return None

    except subprocess.CalledProcessError as e:
        logger.error(f"nvidia-smi failed getting stats: {e.stderr}")
        return None

    except FileNotFoundError:
        logger.error("nvidia-smi not found - cannot get VRAM stats")
        return None

    except (ValueError, IndexError) as e:
        logger.error(
            f"Failed to parse nvidia-smi stats output '{result.stdout}': {e}"
        )
        return None

    except Exception as e:
        logger.error(f"Unexpected error getting VRAM stats: {e}")
        return None


# VRAM estimates by model type (for job metadata enrichment)
# These are estimates - actual usage varies by workflow
VRAM_ESTIMATES = {
    'flux2-klein-9b': 18432,      # 18GB - Flux.2 Klein 9B text-to-image
    'flux2-klein-4b': 8192,       # 8GB - Flux.2 Klein 4B text-to-image
    'ltx2-19b': 24576,            # 24GB - LTX-2 19B text-to-video
    'ltx2-distilled': 12288,      # 12GB - LTX-2 Distilled LoRA
    'default': VRAM_DEFAULT_ESTIMATE_MB  # 8GB - Conservative fallback
}


def estimate_vram_for_model(model_type: str) -> int:
    """
    Get VRAM estimate for known model types.

    Args:
        model_type: Model identifier (e.g., 'ltx2-19b', 'flux2-klein-9b')

    Returns:
        Estimated VRAM requirement in MB

    Example:
        >>> est = estimate_vram_for_model('ltx2-19b')
        >>> print(f"Estimated: {est}MB")  # 24576MB

    Note:
        Returns default estimate (8GB) for unknown models.
        Frontend should provide estimates when possible for accuracy.
    """
    estimate = VRAM_ESTIMATES.get(model_type.lower(), VRAM_ESTIMATES['default'])

    logger.debug(
        f"VRAM estimate for model '{model_type}': {estimate}MB"
    )

    return estimate


if __name__ == "__main__":
    """
    Simple CLI for testing VRAM monitoring.

    Usage:
        python3 vram_monitor.py                    # Show current VRAM stats
        python3 vram_monitor.py check 24576        # Check if 24GB available
        python3 vram_monitor.py estimate ltx2-19b  # Get model estimate
    """
    import sys

    # Set up basic logging for CLI
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    if len(sys.argv) == 1:
        # No args: show VRAM stats
        print("GPU VRAM Status:")
        print("-" * 50)

        stats = get_vram_stats()
        if stats:
            print(f"GPU {stats['gpu_id']}:")
            print(f"  Total:  {stats['total_mb']:,} MB")
            print(f"  Used:   {stats['used_mb']:,} MB")
            print(f"  Free:   {stats['free_mb']:,} MB")
            print(f"  Usage:  {stats['usage_percent']}%")
        else:
            print("ERROR: Could not get VRAM stats")
            sys.exit(1)

    elif len(sys.argv) >= 2 and sys.argv[1] == "check":
        # Check if sufficient VRAM
        required = int(sys.argv[2]) if len(sys.argv) > 2 else 8192

        print(f"Checking VRAM for job requiring {required}MB...")
        print("-" * 50)

        if check_vram_sufficient(required):
            print("✅ SUFFICIENT VRAM")
            sys.exit(0)
        else:
            print("❌ INSUFFICIENT VRAM")
            sys.exit(1)

    elif len(sys.argv) >= 2 and sys.argv[1] == "estimate":
        # Get model estimate
        model = sys.argv[2] if len(sys.argv) > 2 else "default"

        estimate = estimate_vram_for_model(model)
        print(f"VRAM estimate for '{model}': {estimate}MB ({estimate/1024:.1f}GB)")
        sys.exit(0)

    else:
        print("Usage:")
        print("  python3 vram_monitor.py                    # Show VRAM stats")
        print("  python3 vram_monitor.py check <MB>         # Check if sufficient")
        print("  python3 vram_monitor.py estimate <model>   # Get model estimate")
        sys.exit(1)
