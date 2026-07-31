from .models import AuditLog

def generate_diff_summary(old_value, new_value, prefix=""):
    """
    Recursively compares old_value and new_value dicts and generates a list of string summaries.
    """
    summary = []
    
    if not isinstance(old_value, dict) or not isinstance(new_value, dict):
        if old_value != new_value:
            name = prefix.strip('.') or "Value"
            summary.append(f"{name} changed from {old_value} to {new_value}")
        return summary

    all_keys = set(old_value.keys()).union(set(new_value.keys()))
    
    for key in all_keys:
        old_v = old_value.get(key)
        new_v = new_value.get(key)
        current_prefix = f"{prefix}{key}." if prefix else f"{key}."
        
        if isinstance(old_v, dict) and isinstance(new_v, dict):
            summary.extend(generate_diff_summary(old_v, new_v, current_prefix))
        elif old_v != new_v:
            name = current_prefix.rstrip('.')
            if old_v is None:
                summary.append(f"Added {name} with value {new_v}")
            elif new_v is None:
                summary.append(f"Removed {name} (was {old_v})")
            else:
                try:
                    if float(new_v) > float(old_v):
                        summary.append(f"{name} increased from {old_v} to {new_v}")
                    else:
                        summary.append(f"{name} decreased from {old_v} to {new_v}")
                except (ValueError, TypeError):
                    summary.append(f"{name} changed from {old_v} to {new_v}")
                    
    return summary

def create_audit_log(user, module, action, ip_address, user_agent, old_value, new_value):
    """
    Helper function to create an AuditLog entry.
    """
    summary = generate_diff_summary(old_value, new_value)
    
    # Only create if there's an actual change
    if not summary:
        return None
        
    log = AuditLog(
        user_id=user.id if user and user.is_authenticated else None,
        user_email=user.email if user and user.is_authenticated else None,
        module=module,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        old_value=old_value,
        new_value=new_value,
        summary=summary
    )
    log.save()
    return log
