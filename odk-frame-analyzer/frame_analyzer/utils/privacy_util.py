from typing import Dict, List


def not_only_privacy_objects(counts: Dict[str, int]) -> bool:
    """Know if a frame has more then just privacy objects,
    so therefor is relevant to store (by default).

    Args:
        counts (Dict[str, int]): Count as retrieved in AnalyzedFrame

    Returns:
        bool: True = has more then just privacy objects
        False = only has privacy objects
    """
    # If there are no objects cancel
    total_count = counts.get('total')
    if type(total_count) != int:
        return False
    if total_count <= 0:
        return False

    # Setup for determination
    del counts['total']
    privacy_flag = False
    others_flag = False
    
    # Check every count 
    for k, v in counts.items():
        # If a privacy object is found, set privacy flag to True
        if (k == 'face_privacy_filter' or k == 'license_plate_privacy_filter') and v > 0:
            privacy_flag = True
        
        # If anything other then a privacy object is found, set other flag True
        if k != 'face_privacy_filter' and k != 'license_plate_privacy_filter' and v > 0:
            others_flag = True

    # If there are privacy objects, but no 'normal' objects, return False
    if privacy_flag is True and others_flag is False:
        return False
    # If there are privacy objects AND 'normal' objects, return True
    if privacy_flag is False and others_flag is False:
        return False
    # In any other case, return True
    else:
        return True
