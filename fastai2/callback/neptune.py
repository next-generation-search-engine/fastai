# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/72_callback.neptune.ipynb (unless otherwise specified).

__all__ = ['NeptuneCallback']

# Cell
import tempfile
from ..basics import *
from ..learner import Callback

# Cell
import neptune

# Cell
class NeptuneCallback(Callback):
    "Log losses, metrics, model weights, model architecture summary to neptune"
    def __init__(self, log_model_weights=True, keep_experiment_running=False):
        self.log_model_weights = log_model_weights
        self.keep_experiment_running = keep_experiment_running
        self.experiment = None

        if neptune.project is None:
            raise ValueError('You did not initialize project in neptune.\n',
                             'Please invoke `neptune.init("USERNAME/PROJECT_NAME")` before this callback.')

    def begin_fit(self):
        try:
            self.experiment = neptune.get_experiment()
        except ValueError:
            print('No active experiment. Please invoke `neptune.create_experiment()` before this callback.')

        try:
            self.experiment.set_property('n_epoch', str(self.learn.n_epoch))
            self.experiment.set_property('model_class', str(type(self.learn.model)))
        except:
            print(f'Did not log all properties. Check properties in the {neptune.get_experiment()}.')

        try:
            with tempfile.NamedTemporaryFile(mode='w') as f:
                with open(f.name, 'w') as g:
                    g.write(repr(self.learn.model))
                self.experiment.log_artifact(f.name, 'model_summary.txt')
        except:
            print('Did not log model summary. Check if your model is PyTorch model.')

        if self.log_model_weights and not hasattr(self.learn, 'save_model'):
            print('Unable to log model to Neptune.\n',
                  'Use "SaveModelCallback" to save model checkpoints that will be logged to Neptune.')

    def after_batch(self):
        # log loss and opt.hypers
        self.experiment.set_property('n_iter', str(self.learn.n_iter))
        if self.learn.training:
            self.experiment.log_metric('batch__smooth_loss', self.learn.smooth_loss)
            self.experiment.log_metric('batch__loss', self.learn.loss)
            self.experiment.log_metric('batch__train_iter', self.learn.train_iter)
            for i, h in enumerate(self.learn.opt.hypers):
                for k, v in h.items():
                    self.experiment.log_metric(f'batch__opt.hypers.{k}', v)

    def after_epoch(self):
        # log metrics
        for n, v in zip(self.learn.recorder.metric_names, self.learn.recorder.log):
            if n not in ['epoch', 'time']:
                self.experiment.log_metric(f'epoch__{n}', v)
            if n == 'time':
                self.experiment.log_text(f'epoch__{n}', str(v))

        # log model weights
        if self.log_model_weights and hasattr(self.learn, 'save_model'):
            if self.learn.save_model.every_epoch:
                _file = join_path_file(f'{self.learn.save_model.fname}_{self.learn.save_model.epoch}',
                                       self.learn.path / self.learn.model_dir,
                                       ext='.pth')
            else:
                _file = join_path_file(self.learn.save_model.fname,
                                       self.learn.path / self.learn.model_dir,
                                       ext='.pth')
            self.experiment.log_artifact(_file)

    def after_fit(self):
        if not self.keep_experiment_running:
            try:
                self.experiment.stop()
            except:
                print('No neptune experiment to stop.')
        else:
            print(f'Your experiment (id: {self.experiment.id}, name: {self.experiment.name}) is left in the running state.\n',
                  'You can log more data to it, like this: `neptune.log_metric()`')
