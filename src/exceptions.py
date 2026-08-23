class AnomalyDetectionError(Exception):
    """Base class for all custom exceptions in this project."""
    pass

class ModelNotFoundError(AnomalyDetectionError):
    """Raised when saved model artifacts don't exist on disk yet."""
    pass

class InvalidRecordError(AnomalyDetectionError):
    """Raised when an incoming record is missing fields, has the wrong
    type, or otherwise can't be preprocessed."""
    pass

class PreprocessingError(AnomalyDetectionError):
    """Raised when encoding/scaling/PCA-transforming a record fails
    for a reason other than obviously-missing fields (e.g. a value
    that can't be cast to the expected type)."""
    pass


class DataDownloadError(AnomalyDetectionError):
    """Raised when the NSL-KDD dataset can't be downloaded."""
    pass