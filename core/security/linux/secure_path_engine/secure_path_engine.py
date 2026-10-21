from dataclasses import dataclass
import os
from typing import Any

from report_status import report_status  # type: ignore[import-not-found]
from run_secure_cmd import run_secure_cmd  # type: ignore[import-not-found]


# SYSTEM PATH RESOLUTION EXCEPTION CLASS
# Custom exception domain class used to signal when a required file or path cannot be found.
# Standardizes path resolution error formatting across CLI workflows to enable graceful handling without raw stack traces.
class PathResolutionError(Exception):
    """Raised when a required file or path cannot be resolved or is missing."""

    def __init__(self, filename: str, message: str = "Path resolution failure."):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes path error message with standard system tag and filename before delegating to BaseException initializer.
        target_file = filename if filename else "Target path"
        super().__init__(f"Operation Failed: {message} -> {target_file} is missing.")
        self.filename = filename


# ARCHITECTURAL CONFIGURATION GATEWAY: FILESYSTEM SECURITY POLICY SCHEMA
# Encapsulates granular security parameters, permission masks, access control lists,
# and low-level system attributes into a structured, type-safe policy container.
# Decouples runtime execution inputs from baseline filesystem hardening configurations.
@dataclass
class PathSecurityConfig:
    """Encapsulates security policy settings for filesystem hardening.

    Args:
        is_directory: Explicit flag indicating if the target is a directory.
        owner_type: Specifies the owner type ("user" or "root").
        mode: Base POSIX permission mode string (e.g., "700").
        special_mode: Optional special permission bits (e.g., setuid/setgid/sticky).
        user_acl: Optional user-specific access control list specification.
        group_acl: Optional group-specific access control list specification.
        target_group_acl_name: Name of the target group for ACL application.
        acl_mask: Optional mask specification for ACL permissions.
        file_attributes: Low-level file attributes managed via chattr.
        smart_exec: If True, automatically ensures read-enabled directories retain execute bits.
        mac_context: Mandatory Access Control (SELinux) context label.
        preserve_inheritance: If True, preserves inherited access control lists.
    """

    is_directory: bool | None = None
    owner_type: str = "user"
    mode: str = "700"
    special_mode: str | None = None
    user_acl: str | None = None
    group_acl: str | None = None
    target_group_acl_name: str | None = None
    acl_mask: str | None = None
    file_attributes: str | None = None
    smart_exec: bool = True
    mac_context: str | None = None
    preserve_inheritance: bool = True


# ARCHITECTURAL GATEKEEPER: DECOUPLED FILESYSTEM SUPERVISOR ENGINE
# This security engine enforces granular filesystem policies on targets using a structured configuration[cite: 1].
# By coordinating POSIX file permissions, POSIX access control lists (ACLs),
# chattr attributes, and SELinux/MAC contexts, it guarantees consistent system states
# and prevents unauthorized access across volatile runtime paths[cite: 1].
def secure_path_engine(
    ctx: dict[str, Any],
    bins: dict[str, str],
    path: str,
    config: PathSecurityConfig | None = None,
) -> int:
    """Enforces a strict security state on filesystem objects using a structured configuration object.

    Args:
        ctx: Runtime context dictionary containing identity and environment details.
        bins: Dictionary mapping binary names to absolute executable paths.
        path: Target filesystem path to harden.
        config: Optional PathSecurityConfig instance containing hardening policy rules.

    Returns:
        An integer status code (0 on successful completion).
    """
    # Use default security configuration if none was explicitly provided
    cfg = config if config is not None else PathSecurityConfig()

    # PATH INTEGRITY CHECK & ARGUMENT VALIDATION
    # Validates input target string to prevent null or empty filesystem paths.
    if not path:
        raise PathResolutionError(path, "Invalid path reference")

    # ATOMIC RESOURCE INITIALIZATION & JUST-IN-TIME PROVISIONING
    # Evaluates targeted filesystem nodes, provisioning directory hierarchies or bare files
    # with baseline restrictive permissions if the path does not exist.
    if not os.path.exists(path):
        create_as_dir: bool = (
            cfg.is_directory if cfg.is_directory is not None else path.endswith("/")
        )

        if create_as_dir:
            os.makedirs(path, mode=0o700, exist_ok=True)
        else:
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, mode=0o700, exist_ok=True)
            with open(path, "a"):
                os.utime(path, None)

    # FILESYSTEM INSTANTIATION VERIFICATION
    # Confirms physical presence of target path before proceeding with permission execution passes.
    if not os.path.exists(path):
        raise PathResolutionError(path, "Failed to provision target object")

    is_dir: bool = os.path.isdir(path)

    # PRIVILEGED IDENTITY RESOLUTION & UID MAPPING
    # Maps user context permissions to standard runtime UID or superuser identity.
    target_uid: int = (
        0 if cfg.owner_type == "root" and ctx.get("is_privileged") else ctx["uid"]
    )

    # DIRECTORY SMART EXECUTABILITY & TRAVERSAL SAFEGUARD
    # Evaluates directory flags to ensure read-enabled directories retain mandatory execute bits
    # for valid filesystem traversal without granting broad permission escalations.
    processed_mode = cfg.mode
    if is_dir and cfg.smart_exec:
        mode_digits = [int(d) for d in cfg.mode]
        if len(mode_digits) == 3 and (mode_digits[0] & 4) and not (mode_digits[0] & 1):
            mode_digits[0] |= 1
            processed_mode = "".join(str(d) for d in mode_digits)

    final_mode: str = (
        f"{cfg.special_mode}{processed_mode}" if cfg.special_mode else processed_mode
    )

    # BASELINE PERMISSION ENFORCEMENT & POSIX HARDENING
    # Applies underlying ownership assignments and standard POSIX permission masks.
    run_secure_cmd(ctx, [bins["CHOWN"], f"{target_uid}:{ctx['target_gid']}", path])
    run_secure_cmd(ctx, [bins["CHMOD"], final_mode, path])

    # ACL INHERITANCE MANAGEMENT & GHOSTING CONTROL
    # Strips inherited standard ACLs when requested to isolate target object security contexts.
    if not cfg.preserve_inheritance:
        run_secure_cmd(ctx, [bins["SETFACL"], "-b", path])

    acl_parts: list[str] = []

    # DYNAMIC USER ACL HARDENING & DIRECTORY INHERITANCE
    # Sets granular user access controls across object handles and default directory specs.
    if cfg.user_acl:
        user_spec: str = f"u:{ctx['user']}:{cfg.user_acl}"
        run_secure_cmd(ctx, [bins["SETFACL"], "-m", user_spec, path])
        if is_dir:
            default_user_spec: str = f"d:u:{ctx['user']}:{cfg.user_acl}"
            run_secure_cmd(ctx, [bins["SETFACL"], "-m", default_user_spec, path])
        acl_parts.append(f"UserACL: {cfg.user_acl}")

    # DYNAMIC GROUP ACL HARDENING & INHERITANCE
    # Sets target group permission specs across current target and underlying directory defaults.
    if cfg.group_acl:
        grp_name = cfg.target_group_acl_name or ctx.get("target_group", "root")
        group_spec: str = f"g:{grp_name}:{cfg.group_acl}"
        run_secure_cmd(ctx, [bins["SETFACL"], "-m", group_spec, path])
        if is_dir:
            default_group_spec: str = f"d:g:{grp_name}:{cfg.group_acl}"
            run_secure_cmd(ctx, [bins["SETFACL"], "-m", default_group_spec, path])
        acl_parts.append(f"GroupACL({grp_name}): {cfg.group_acl}")

    # EXPLICIT MASK CONTROL & PERMISSION CEILING
    # Applies limiting mask specifications to control maximum calculated effective permissions.
    if cfg.acl_mask:
        mask_spec: str = f"m:{cfg.acl_mask}"
        run_secure_cmd(ctx, [bins["SETFACL"], "-m", mask_spec, path])
        if is_dir:
            default_mask_spec: str = f"d:m:{cfg.acl_mask}"
            run_secure_cmd(ctx, [bins["SETFACL"], "-m", default_mask_spec, path])
        acl_parts.append(f"Mask: {cfg.acl_mask}")

    acl_msg: str = ", ".join(acl_parts) if acl_parts else "standard perms"

    # EXTENDED FILE ATTRIBUTES ENFORCEMENT
    # Invokes chattr binaries to set low-level file attributes (e.g., append-only, immutable).
    attr_msg: str = ""
    if cfg.file_attributes and "CHATTR" in bins:
        run_secure_cmd(ctx, [bins["CHATTR"], cfg.file_attributes, path])
        attr_msg = f"Attr: {cfg.file_attributes}"

    # MANDATORY ACCESS CONTROL (MAC) CONTEXT ASSIGNMENT
    # Assigns targeted SELinux/MAC context labels to enforce system security policies.
    mac_msg: str = ""
    if cfg.mac_context and "CHCON" in bins:
        run_secure_cmd(ctx, [bins["CHCON"], cfg.mac_context, path])
        mac_msg = f"MAC: {cfg.mac_context}"

    # TELEMETRY & AUDIT LOGGING PIPELINE
    # Writes hardened path metadata and dynamic status metrics to standard error outputs.
    path_label: str = "DIR" if is_dir else "FILE"
    display_owner: str = "root" if target_uid == 0 else ctx["user"]

    extra_details = f" | {attr_msg}" if attr_msg else ""
    if mac_msg:
        extra_details += f" | {mac_msg}"

    report_status(
        state="done",
        message=f"Hardened {path_label}: {path} ({display_owner}:{ctx['target_group']}, "
        f"{final_mode}) [{acl_msg}]{extra_details}",
    )

    return 0
