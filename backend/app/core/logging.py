import logging
import sys
import structlog
from asgi_correlation_id import correlation_id

def configure_logging():
    """
    Configure structured logging with structlog.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
    ]

    # Add correlation ID if available
    def add_correlation(logger, log_method, event_dict):
        request_id = correlation_id.get()
        if request_id:
            event_dict["request_id"] = request_id
        return event_dict

    shared_processors.insert(1, add_correlation)

    structlog.configure(
        processors=shared_processors + [
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure Standard Library Logging to use Structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Silence noisy libraries
    logging.getLogger("uvicorn.access").disabled = True # We can use our own or let uvicorn log JSON if configured
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

logger = structlog.get_logger()
