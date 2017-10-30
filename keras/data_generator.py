"""Define DataGenerator class

Author: Stephan Rasp
"""

import numpy as np
import h5py


class DataSet(object):
    """Gets a dataset of train data.
    """

    def __init__(self, data_dir, out_fn, mean_fn, std_fn, feature_names,
                 target_names=['SPDT', 'SPDQ'],
                 convolution=False, dtype='float32'):
        """
        Initialize dataset
        Args:
            data_dir: directory where data is stored
            out_fn: filename of outputs file
            mean_fn: filename of mean file
            std_fn: filename of std file
            target_names: target variable names
            convolution: get data with channels
            dtype: numpy precision
        """
        # File names
        self.data_dir = data_dir
        self.out_fn = data_dir + out_fn
        self.mean_fn = data_dir + mean_fn
        self.std_fn = data_dir + std_fn

        # Other settings
        self.convolution = convolution
        self.feature_names = feature_names
        self.target_names = target_names
        self.dtype = dtype

        # Load data
        self.features = self.__get_features()
        self.targets = self.__get_targets()

    # These functions are copied from the data generator function
    def __get_features(self):
        """Load and scale the features
        """
        # Load features
        with h5py.File(self.out_fn, 'r') as out_file, \
                h5py.File(self.mean_fn, 'r') as mean_file, \
                h5py.File(self.std_fn, 'r') as std_file:

            # Get total number of samples
            self.n_samples = out_file['TAP'].shape[1]

            f_list = []
            for v in self.feature_names:
                f = np.atleast_2d(out_file[v][:]).T
                # normalize
                f = (f - mean_file[v].value) / std_file[v].value
                # Adjust data type
                f = np.asarray(f, dtype=self.dtype)
                f_list.append(f)
            if self.convolution:
                f_2d = [f for f in f_list if f.shape[1] > 1]
                f_1d = [f for f in f_list if f.shape[1] == 1]
                f_2d = np.stack(f_2d, axis=-1)
                # I do not think this is necessary!
                # f_2d = np.reshape(
                #     f_2d, (f_2d.shape[0], f_2d.shape[1], 1, f_2d.shape[2])
                # )
                f_1d = np.concatenate(f_1d, axis=1)
                return [f_2d, f_1d]
                # [sample, z, feature]
            else:
                return np.concatenate(f_list, axis=1)
                # [sample, flattened features]

    def __get_targets(self):
        """Load and convert the targets
        """
        with h5py.File(self.out_fn, 'r') as out_file:
            targets = np.concatenate([
                out_file['SPDT'][:] * 1000.,
                out_file['SPDQ'][:] * 2.5e6,
            ], axis=0)
            return np.asarray(targets.T, dtype=self.dtype)


class DataGenerator(object):
    """Generate batches
    https://stanford.edu/~shervine/blog/keras-how-to-generate-data-on-the-fly.html
    Note that this function loads the entire dataset into RAM.
    This can be quite memory intensive!
    """

    def __init__(self, data_dir, out_name, batch_size, feature_names,
                 target_names=['SPDT', 'SPDQ'],
                 shuffle_mode='batches',
                 convolution=False):
        """Initialize generator
        If shuffle_mode is "batches", only the order of the batches will be shuffled.
        If it is something else, everything will be shuffled, but this is much much much
        slower!
        """
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.shuffle_mode = shuffle_mode
        self.feature_names = feature_names
        assert target_names == ['SPDT', 'SPDQ'], 'No other targets implemented.'
        self.target_names = target_names
        self.convolution = convolution

        # Open files
        self.out_fn = data_dir + out_name
        self.mean_fn = data_dir + 'SPCAM_mean.nc'
        self.std_fn = data_dir + 'SPCAM_std.nc'

        # Load features
        self.features = self.__get_features()
        self.targets = self.__get_targets()

        # Determine sizes

        self.n_batches = int(self.n_samples / batch_size)

        # Create ID list
        if self.shuffle_mode == 'batches':
            self.idxs = np.arange(0, self.n_samples, self.batch_size)
        else:
            self.idxs = np.arange(self.n_samples)

    def generate(self, shuffle=True):
        """Generate data batches
        """
        gen_idxs = np.copy(self.idxs)
        if shuffle:
            np.random.shuffle(gen_idxs)

        while True:
            for i in range(self.n_batches):
                if self.shuffle_mode == 'batches':
                    batch_idx = gen_idxs[i]
                    if self.convolution:
                        x = [
                            self.features[0][batch_idx:batch_idx + self.batch_size],
                            self.features[1][batch_idx:batch_idx + self.batch_size]
                        ]
                    else:
                        x = self.features[batch_idx:batch_idx + self.batch_size]
                    y = self.targets[batch_idx:batch_idx + self.batch_size]
                else:
                    batch_idx = [self.idxs[k] for k in
                        self.idxs[i * self.batch_size:(i + 1) * self.batch_size]]
                    if self.convolution:
                        x = [
                            self.features[0][batch_idx],
                            self.features[1][batch_idx]
                        ]
                    else:
                        x = self.features[batch_idx]
                    y = self.targets[batch_idx]

                yield x, y

    def __get_features(self):
        """Load and scale the features
        """
        # Load features
        with h5py.File(self.out_fn, 'r') as out_file, \
             h5py.File(self.mean_fn, 'r') as mean_file, \
             h5py.File(self.std_fn, 'r') as std_file:

            # Get total number of samples
            self.n_samples = out_file['TAP'].shape[1]

            f_list = []
            for v in self.feature_names:
                f = np.atleast_2d(out_file[v][:]).T
                # normalize
                f = (f - mean_file[v].value) / std_file[v].value
                f_list.append(f)
            if self.convolution:
                f_2d = [f for f in f_list if f.shape[1] > 1]
                f_1d = [f for f in f_list if f.shape[1] == 1]
                f_2d = np.stack(f_2d, axis=-1)
                # I do not think this is necessary!
                # f_2d = np.reshape(
                #     f_2d, (f_2d.shape[0], f_2d.shape[1], 1, f_2d.shape[2])
                # )
                f_1d = np.concatenate(f_1d, axis=1)
                return [f_2d, f_1d]
                # [sample, z, feature]
            else:
                return np.concatenate(f_list, axis=1)
                # [sample, flattened features]

    def __get_targets(self):
        """Load and convert the targets
        """
        with h5py.File(self.out_fn, 'r') as out_file:
            targets = np.concatenate([
                out_file['SPDT'][:] * 1000.,
                out_file['SPDQ'][:] * 2.5e6,
            ], axis=0)
            return targets.T
