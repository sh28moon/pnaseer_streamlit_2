# modules/storage_utils.py
import json
import os
import pandas as pd
from datetime import datetime

def serialize_dataframe(df):
    """Safely serialize a DataFrame to dict"""
    if df is None:
        return None
    if hasattr(df, 'to_dict'):
        return df.to_dict('records')
    return df

def deserialize_dataframe(data):
    """Safely deserialize dict to DataFrame"""
    if data is None:
        return None
    if isinstance(data, list):
        return pd.DataFrame(data)
    return data

def serialize_complex_data(data):
    """Recursively serialize complex data structures including nested DataFrames"""
    if data is None:
        return None
    
    # Handle pandas DataFrame
    if hasattr(data, 'to_dict'):
        return {"__dataframe__": data.to_dict('records')}
    
    # Handle dictionaries
    if isinstance(data, dict):
        serialized_dict = {}
        for key, value in data.items():
            serialized_dict[key] = serialize_complex_data(value)
        return serialized_dict
    
    # Handle lists
    if isinstance(data, list):
        return [serialize_complex_data(item) for item in data]
    
    # Handle tuples
    if isinstance(data, tuple):
        return {"__tuple__": [serialize_complex_data(item) for item in data]}
    
    # Handle numpy arrays
    if hasattr(data, 'tolist'):
        return {"__numpy_array__": data.tolist()}
    
    # Handle other types that might not be JSON serializable
    try:
        import json
        json.dumps(data)  # Test if it's JSON serializable
        return data
    except (TypeError, ValueError):
        # If not serializable, convert to string representation
        return {"__string_repr__": str(data)}

def deserialize_complex_data(data):
    """Recursively deserialize complex data structures including nested DataFrames"""
    if data is None:
        return None
    
    # Handle dictionaries
    if isinstance(data, dict):
        # Check for special markers
        if "__dataframe__" in data:
            return pd.DataFrame(data["__dataframe__"])
        elif "__tuple__" in data:
            return tuple(deserialize_complex_data(item) for item in data["__tuple__"])
        elif "__numpy_array__" in data:
            import numpy as np
            return np.array(data["__numpy_array__"])
        elif "__string_repr__" in data:
            return data["__string_repr__"]  # Return as string, can't reconstruct original object
        else:
            # Regular dictionary
            deserialized_dict = {}
            for key, value in data.items():
                deserialized_dict[key] = deserialize_complex_data(value)
            return deserialized_dict
    
    # Handle lists
    if isinstance(data, list):
        return [deserialize_complex_data(item) for item in data]
    
    # Return as-is for basic types
    return data

def save_data_to_file(data, data_type, save_name):
    """Generic function to save any data to JSON file
    
    Args:
        data: Data to save (dict, job object, etc.)
        data_type: Type of data ('datasets', 'jobs', etc.)
        save_name: Name for the saved file
    
    Returns:
        tuple: (success: bool, result: str)
    """
    try:
        # Create directory if it doesn't exist
        directory = f"saved_{data_type}"
        os.makedirs(directory, exist_ok=True)
        
        # Prepare save data structure
        save_data = {
            "save_name": save_name,
            "data_type": data_type,
            "saved_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # Handle different data types
        if data_type == "datasets":
            # For datasets: data is a dict of DataFrames, save_name format: "dataset_type_name"
            dataset_data = {}
            for name, df in data.items():
                dataset_data[name] = serialize_complex_data(df)
            save_data["datasets"] = dataset_data
            save_data["dataset_count"] = len(dataset_data)
            
            # Extract dataset_type from save_name (format: "dataset_type_actual_name")
            if "_" in save_name:
                dataset_type_part = save_name.split("_", 1)[0]  # Get first part as dataset_type
                actual_save_name = save_name.split("_", 1)[1]   # Get rest as actual name
                save_data["dataset_type"] = dataset_type_part
                save_data["save_name"] = actual_save_name
            else:
                save_data["dataset_type"] = "unknown"
            
        elif data_type == "jobs":
            # For jobs: data is a Job object (no longer includes databases)
            job = data
            save_data.update({
                "name": job.name,
                "created_at": job.created_at,
                "api_dataset": serialize_complex_data(job.api_dataset),
                "target_profile_dataset": serialize_complex_data(job.target_profile_dataset),
                "model_dataset": serialize_complex_data(job.model_dataset),
                "result_dataset": serialize_complex_data(job.result_dataset),
            })
            
            # Handle complete target profiles (these reference global databases but don't own them)
            save_data["complete_target_profiles"] = {}
            if hasattr(job, 'complete_target_profiles') and job.complete_target_profiles:
                for profile_name, profile_data in job.complete_target_profiles.items():
                    save_data["complete_target_profiles"][profile_name] = serialize_complex_data(profile_data)
            
            # Handle results and optimization progress - use complex serialization for results
            save_data["formulation_results"] = serialize_complex_data(getattr(job, 'formulation_results', {}))
            save_data["optimization_progress"] = serialize_complex_data(getattr(job, 'optimization_progress', {}))
            save_data["current_optimization_progress"] = serialize_complex_data(getattr(job, 'current_optimization_progress', None))
        
        # Save to file
        filename = f"{directory}/{data_type}_{save_name}.json"
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return True, filename
    except Exception as e:
        return False, str(e)

def load_data_from_file(filepath, data_type):
    """Generic function to load data from JSON file
    
    Args:
        filepath: Path to the JSON file
        data_type: Type of data ('datasets', 'jobs', etc.)
    
    Returns:
        tuple: (loaded_data, timestamp, additional_info)
    """
    try:
        with open(filepath, 'r') as f:
            save_data = json.load(f)
        
        saved_timestamp = save_data.get("saved_timestamp", "Unknown")
        
        if data_type == "datasets":
            # Return datasets dict
            loaded_datasets = {}
            for name, records in save_data["datasets"].items():
                loaded_datasets[name] = deserialize_complex_data(records)
            return loaded_datasets, saved_timestamp, save_data.get("dataset_count", 0)
            
        elif data_type == "jobs":
            # Return Job object
            from app import Job
            
            job = Job(save_data["name"])
            job.created_at = save_data["created_at"]
            
            # Restore basic datasets using complex deserialization
            job.api_dataset = deserialize_complex_data(save_data.get("api_dataset"))
            job.target_profile_dataset = deserialize_complex_data(save_data.get("target_profile_dataset"))
            job.model_dataset = deserialize_complex_data(save_data.get("model_dataset"))
            job.result_dataset = deserialize_complex_data(save_data.get("result_dataset"))
            
            # Restore database data
            job.common_api_datasets = {}
            if save_data.get("common_api_datasets"):
                for k, v in save_data["common_api_datasets"].items():
                    job.common_api_datasets[k] = deserialize_complex_data(v)
            
            job.polymer_datasets = {}
            if save_data.get("polymer_datasets"):
                for k, v in save_data["polymer_datasets"].items():
                    job.polymer_datasets[k] = deserialize_complex_data(v)
            
            # Restore complete target profiles
            job.complete_target_profiles = {}
            if save_data.get("complete_target_profiles"):
                for profile_name, profile_data in save_data["complete_target_profiles"].items():
                    job.complete_target_profiles[profile_name] = deserialize_complex_data(profile_data)
            
            # Restore results and optimization progress using complex deserialization
            job.formulation_results = deserialize_complex_data(save_data.get("formulation_results", {}))
            job.optimization_progress = deserialize_complex_data(save_data.get("optimization_progress", {}))
            job.current_optimization_progress = deserialize_complex_data(save_data.get("current_optimization_progress"))
            
            return job, saved_timestamp, len(job.complete_target_profiles)
        
        else:
            return None, saved_timestamp, 0
            
    except Exception as e:
        return None, str(e), 0

def get_saved_data_list(data_type):
    """Get list of saved data files for specific type
    
    Args:
        data_type: Type of data ('datasets', 'jobs', etc.)
    
    Returns:
        list: List of saved file info dicts
    """
    try:
        directory = f"saved_{data_type}"
        if not os.path.exists(directory):
            return []
        
        saved_files = []
        
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = f"{directory}/{filename}"
                
                if data_type == "datasets":
                    # For datasets: filename format is "dataset_type_name.json"
                    # Extract save_name as the full filename without .json
                    save_name = filename[:-5]  # Remove .json
                else:
                    # For jobs: filename format is "jobs_name.json" 
                    prefix = f"{data_type}_"
                    if filename.startswith(prefix):
                        save_name = filename[len(prefix):-5]  # Remove prefix and .json
                    else:
                        continue  # Skip files that don't match expected pattern
                
                try:
                    # Test if the file is valid JSON
                    with open(filepath, 'r') as f:
                        json.load(f)
                    
                    # Get file modification time
                    mtime = os.path.getmtime(filepath)
                    saved_files.append({
                        "save_name": save_name,
                        "filename": filename,
                        "filepath": filepath,
                        "modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
                except (json.JSONDecodeError, Exception):
                    # Skip corrupted files
                    continue
        
        # Sort by modification time (newest first)
        saved_files.sort(key=lambda x: x["modified"], reverse=True)
        return saved_files
    except Exception:
        return []

def get_saved_datasets_by_type(dataset_type):
    """Get list of saved dataset files filtered by dataset type
    
    Args:
        dataset_type: Type of dataset ('common_api', 'polymer', etc.)
    
    Returns:
        list: List of filtered dataset file info dicts
    """
    all_datasets = get_saved_data_list("datasets")
    filtered_datasets = []
    
    prefix = f"{dataset_type}_"
    for dataset in all_datasets:
        if dataset["save_name"].startswith(prefix):
            # Create a copy with the display name (without prefix)
            filtered_dataset = dataset.copy()
            filtered_dataset["display_name"] = dataset["save_name"][len(prefix):]
            filtered_datasets.append(filtered_dataset)
    
    return filtered_datasets

def delete_saved_data(filepath):
    """Delete a saved data file
    
    Args:
        filepath: Path to the file to delete
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        os.remove(filepath)
        return True, "File deleted successfully"
    except Exception as e:
        return False, str(e)

# Add "Save Progress" and "Clear Progress" button functions
def save_progress_to_job(current_job):
    """Save progress function that acts same as 'Save to Cloud' button in Job Management
    
    Args:
        current_job: Current job object to save
    
    Returns:
        tuple: (success: bool, result: str)
    """
    if not current_job:
        return False, "No current job to save"
    
    try:
        # Ensure all job attributes exist
        from app import ensure_job_attributes
        current_job = ensure_job_attributes(current_job)
        
        # Save job using unified storage
        success, result = save_data_to_file(current_job, "jobs", current_job.name)
        return success, result
    except Exception as e:
        return False, str(e)

def clear_progress_from_job(current_job):
    """Clear progress function to clear optimization progress
    
    Args:
        current_job: Current job object to clear progress from
    
    Returns:
        tuple: (success: bool, result: str)
    """
    if not current_job:
        return False, "No current job to clear"
    
    try:
        # Clear optimization progress
        if hasattr(current_job, 'current_optimization_progress'):
            current_job.current_optimization_progress = None
        if hasattr(current_job, 'optimization_progress'):
            current_job.optimization_progress = {}
        
        return True, "Progress cleared successfully"
    except Exception as e:
        return False, str(e)
