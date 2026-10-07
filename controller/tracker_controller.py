from logger import logger
from controller.auth_controller import AuthController


class HardwareAuthController(AuthController):
    """Authentication controller used by the hardware inventory views."""

    def login(self, username, password):
        success, result = super().login(username, password)
        if not success:
            logger.warning(
                "Failed login attempt for username='%s': %s",
                username,
                result,
            )
        return success, result

    def register(self, username, password, email=None, role="USER"):
        success, msg = super().register(
            username,
            password,
            email=email,
            role=role,
        )

        if not success:
            logger.warning(
                "Failed registration attempt: username='%s', email='%s' - %s",
                username,
                email,
                msg,
            )
        return success, msg

    def logout(self, username="Unknown"):
        logger.info("User Logged Out: '%s'", username)
        return True, "Logged out successfully."
