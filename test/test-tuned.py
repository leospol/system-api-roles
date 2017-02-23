
import machine
import re
from avocado.utils import process


class TestTuned(machine.Test):

    """
    :avocado: enable
    """

    def test(self):
        for profile in ('balanced', 'powersave', 'throughput-performance',
                        'latency-performance'):
            self.machine.set_config('com.redhat.tuned', profile=profile)

        self.machine.set_config('com.redhat.tuned',
                                use_recommended_profile=True)
