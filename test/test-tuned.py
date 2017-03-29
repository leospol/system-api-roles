import machine


class TestTuned(machine.Test):

    """
    :avocado: enable
    """

    def test(self):
        for profile in ('balanced', 'powersave', 'throughput-performance',
                        'latency-performance', 'virtual-guest', 'virtual-host'):
            self.machine.set_config('com.redhat.tuned', profile=profile,
                                    test_tasks_file='main.yml')

        self.machine.set_config('com.redhat.tuned',
                                use_recommended_profile=True,
                                test_tasks_file='main.yml')
