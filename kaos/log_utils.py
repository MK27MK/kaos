import logging

# ANSI codes for colors and bold
RESET = "\033[0m"
BOLD = "\033[1m"
COLORS = {
    "DEBUG": "\033[34m",  # blue
    "INFO": "\033[32m",  # green
    "WARNING": "\033[33m",  # yellow
    "ERROR": "\033[31m",  # red
    "CRITICAL": "\033[35m",  # purple
}
WHITE_BOLD = "\033[1;37m"  # bold white


class ColorFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname.ljust(8)  # padding for critical(the longest)
        color = COLORS.get(record.levelname, "")
        levelname_colored = f"{BOLD}{color}{levelname}{RESET}"
        asctime_colored = f"{WHITE_BOLD}{self.formatTime(record)}{RESET}"
        # separator = f"{BOLD}{RESET}"
        message = record.getMessage()
        return f"{asctime_colored} {levelname_colored} {message}"


# logger function ------------------------------------------------------


def get_logger(name: str, level=logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger
    handler = logging.StreamHandler()
    handler.setFormatter(
        ColorFormatter(
            fmt="{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger.handlers = [handler]
    logger.propagate = False
    return logger


if __name__ == "__main__":
    logger = get_logger("kaos logger")
    logger.debug("A message.")
    logger.info("A message.")
    logger.warning("A message.")
    logger.error("A message.")
    logger.critical("A message.")
