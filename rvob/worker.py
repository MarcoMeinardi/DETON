from multiprocessing import Pool

class Worker:
    def __init__(self, configurations, optimize_overhead, target_heat, original_configuration, configurations_backup, n_threads, Log):
        self.configurations = configurations
        self.total_iterations = len(self.configurations)
        self.optimize_overhead = optimize_overhead
        self.original_configuration = original_configuration
        self.target_heat = target_heat
        if self.optimize_overhead:
            self.best = None
        else:
            self.best = self.original_configuration
        self.configurations_backup = configurations_backup
        self.thread_pool = Pool(n_threads)
        self.Log = Log

    def run(self):
        for configuration in self.configurations:
            self.thread_pool.apply_async(
                configuration.evaluate,
                args = (),
                callback = self.callback
            )
        self.thread_pool.close()
        self.thread_pool.join()
        return self.best

    def callback(self, configuration):
        self.Log.debug(f"Executed with: {configuration} ({configuration.id} / {self.total_iterations})")
        self.Log.debug("New mean heat:", configuration.mean_heat)
        self.Log.debug("Overhead introduced:", configuration.lines_num - self.original_configuration.lines_num)
        self.Log.debug()

        if self.optimize_overhead:
            if configuration.mean_heat >= self.target_heat:
                self.best = configuration
                self.thread_pool.terminate()
        elif configuration.mean_heat > self.best.mean_heat:
            self.best = configuration

        configuration_dict = configuration.__dict__.copy()
        del configuration_dict["input_data"]
        self.configurations_backup.append(configuration_dict)