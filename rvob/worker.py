from multiprocessing import Pool
from logger import INFO
from tqdm import tqdm

class Worker:
    def __init__(self, configurations, optimize_overhead, target_heat, original, configurations_backup, n_threads, Log):
        self.configurations = configurations
        self.total_iterations = len(self.configurations)
        self.optimize_overhead = optimize_overhead
        self.original = original
        self.target_heat = target_heat
        if self.optimize_overhead:
            self.best = None
        else:
            self.best = self.original
        self.configurations_backup = configurations_backup
        self.thread_pool = Pool(n_threads)
        self.Log = Log

    def run(self):
        if self.Log.log_level == INFO:
            self.progress_bar = tqdm(total = self.total_iterations)

        for configuration in self.configurations:
            try:
                self.thread_pool.apply_async(
                    configuration.evaluate,
                    args = (),
                    callback=self.callback
                )
            except ValueError:
                # when optimizing for overhead, it might happen that a solution is found almost immediately,
                # if this happens, the pool get closed and I cannot add tasks to it, raising this error 
                break
        
        self.thread_pool.close()
        self.thread_pool.join()
        if self.Log.log_level == INFO:
            self.progress_bar.close()
            
        return self.best

    def callback(self, configuration):
        self.Log.debug(f"Executed with: {configuration} ({configuration.id} / {self.total_iterations})")
        self.Log.debug("New mean heat:", configuration.mean_heat)
        self.Log.debug("Overhead introduced:", configuration.lines_num - self.original.lines_num)
        self.Log.debug()
        if self.Log.log_level == INFO:
            self.progress_bar.update(1)

        if self.optimize_overhead:
            if configuration.mean_heat >= self.target_heat:
                self.best = configuration
                self.thread_pool.terminate()
                if self.Log.log_level == INFO:
                    self.progress_bar.close()

        elif configuration.mean_heat > self.best.mean_heat:
            self.best = configuration

        configuration_dict = configuration.__dict__.copy()
        del configuration_dict["input_data"]
        self.configurations_backup.append(configuration_dict)