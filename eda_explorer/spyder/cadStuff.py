#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 16:06:04 2025

Basics of Cad tool Support

@author: simonchang
"""


import os
import re
from pathlib import Path
from functools import lru_cache
from typing import Dict, Set, Optional, Union
import inspect
import importlib.util

def full(path):
    """
    Expands a path to its absolute form, resolving home directory (~),
    environment variables, and relative path components.
    
    Args:
        path (str): The path to expand
        
    Returns:
        str: The fully expanded absolute path
    """
    # First expand any environment variables (e.g. $HOME, ${HOME})
    expanded = os.path.expandvars(path)
    
    # Then expand ~ to home directory
    expanded = os.path.expanduser(expanded)
    
    # Finally convert to absolute path, resolving any relative components
    expanded = os.path.abspath(expanded)
    
    return expanded

def expand_env_vars(path: str) -> str:
    """Expand environment variables in a path string."""
    # Handle ${VAR} and $VAR format
    path = re.sub(r'\${([^}]+)}', lambda m: os.environ.get(m.group(1), m.group(0)), path)
    path = re.sub(r'\$([A-Za-z0-9_]+)', lambda m: os.environ.get(m.group(1), m.group(0)), path)
    return path

@lru_cache(maxsize=None)
def parse_cdslib(cdslib_path: str = "$PROJHOME/cds.lib") -> Dict[str, str]:
    """
    Parse a cds.lib file and return a dictionary of library names to their resolved paths.
    Uses caching to avoid re-parsing the same file multiple times.
    
    Args:
        cdslib_path: Path to the cds.lib file
        
    Returns:
        Dictionary mapping library names to their full resolved paths
    """
    libraries = {}
    processed_files = set()  # Track processed files to prevent circular includes
    
    def resolve_path(path: str, relative_to: Path) -> str:
        """Resolve a path, handling both absolute and relative paths."""
        path = expand_env_vars(path)
        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            resolved_path = (relative_to / path).resolve()
        return str(resolved_path)
    
    def process_file(file_path: str, processed: Set[str]) -> None:
        """
        Recursively process a cds.lib file and its includes.
        
        Args:
            file_path: Path to the cds.lib file to process
            processed: Set of already processed file paths
        """
        abs_path = str(Path(file_path).resolve())
        if abs_path in processed:
            return
        
        processed.add(abs_path)
        current_dir = Path(file_path).parent
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    # Remove comments and strip whitespace
                    line = line.split('#')[0].strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    command = parts[0].upper()
                    
                    if command in ('INCLUDE', 'SOFTINCLUDE'):
                        if len(parts) >= 2:
                            include_path = resolve_path(parts[1], current_dir)
                            if os.path.exists(include_path):
                                process_file(include_path, processed)
                    
                    elif command == 'DEFINE':
                        if len(parts) >= 3:
                            lib_name = parts[1]
                            lib_path = resolve_path(' '.join(parts[2:]), current_dir)
                            libraries[lib_name] = lib_path
                    
                    elif command == 'SOFTDEFINE':
                        if len(parts) >= 3:
                            lib_name = parts[1]
                            if lib_name not in libraries:
                                lib_path = resolve_path(' '.join(parts[2:]), current_dir)
                                libraries[lib_name] = lib_path
                    
                    elif command == 'UNDEFINE':
                        if len(parts) >= 2:
                            lib_name = parts[1]
                            libraries.pop(lib_name, None)
        
        except FileNotFoundError:
            print(f"Warning: Could not find file {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    process_file(expand_env_vars(cdslib_path), processed_files)
    return libraries

@lru_cache(maxsize=None)
def isXschem(lib):
    lD=parse_cdslib()
    assert lib in lD
    
    path = Path(lD[lib])
    
    if not path.is_dir():
        return False
    
    # Check for xschemviews directory
    if (path / "xschemviews").is_dir():
        return True
    
    # Check for files with specific extensions
    target_extensions = {".sym", ".sch", ".va"}
    
    # Iterate through files in the directory
    for file_path in path.iterdir():
        if file_path.is_file() and file_path.suffix in target_extensions:
            return True
    
    return False

def getXschemCells(lib):
    """
    Get a list of all cell names in an XSchem library directory.
    
    Args:
        directory_path (str or Path): Path to the XSchem library directory
        
    Returns:
        set: Set of unique cell names found in the directory
    """
    lD=parse_cdslib()
    assert lib in lD    
    path = Path(lD[lib])
    
    cells = set()  # Using a set to automatically handle duplicates
    
    # Check for files with target extensions
    target_extensions = {".sym", ".sch", ".va"}
    for file_path in path.iterdir():
        if file_path.is_file() and file_path.suffix in target_extensions:
            # Add stem (filename without extension) to the set
            cells.add(file_path.stem)
    
    # Check for xschemviews subdirectories if the folder exists
    xschemviews_path = path / "xschemviews"
    if xschemviews_path.is_dir():
        # Add names of all subdirectories in xschemviews
        for subdir in xschemviews_path.iterdir():
            if subdir.is_dir():
                cells.add(subdir.name)
    
    # Convert to sorted list for consistent ordering
    return sorted(list(cells))

def getXschemCellViews(lib, cell_name):
    """
    Get a dictionary of views available for a specific cell in an XSchem library.
    
    Args:
        lib (str or Path): library
        cell_name (str): Name of the cell to find views for
        
    Returns:
        dict: Dictionary mapping view names to their full file paths
    """
    lD=parse_cdslib()
    assert lib in lD    
    lib_path = Path(lD[lib])
    views = {}
    
    # Check for standard views (sch, sym, va)
    standard_views = {
        'sch': lib_path / f"{cell_name}.sch",
        'sym': lib_path / f"{cell_name}.sym",
        'va': lib_path / f"{cell_name}.va"
    }
    
    # Add standard views if they exist
    for view_name, file_path in standard_views.items():
        if file_path.is_file():
            views[view_name] = str(file_path)
    
    # Check for additional views in xschemviews directory
    views_path = lib_path / "xschemviews" / cell_name
    if views_path.is_dir():
        for file_path in views_path.iterdir():
            if file_path.is_file():
                print(file_path)
                view_name = file_path.stem  # Get filename without extension
                views[view_name] = str(file_path)
    
    return views

class oalcv:
    """
    Class to handle Open Access library/cell/view (LCV) triplets.
    If instantiated from within a Open Access cellview, automatically detects the context.
    
    Also handle if it's an XSchem LCV which is somewhat more fiddly...
    
    Args:
        lcv_string: String in format "library/cell" or "library/cell/view"
        default_view: Default view to use if not specified in lcv_string
    """
    def __init__(self, lcv_string: Union[str, 'oalcv'], default_view: Optional[str] = None):
        # Convert input to string if it's another oalcv object
        lcv_string = str(lcv_string)
        
        # Split the input string
        parts = lcv_string.strip().split('/')
        
        if len(parts) < 2:
            raise ValueError(f"Invalid LCV string '{lcv_string}'. Must contain at least library/cell.")
        
        if len(parts) > 3:
            raise ValueError(f"Invalid LCV string '{lcv_string}'. Too many '/' separators.")
            
        # Assign library and cell
        self.lib = parts[0]
        self.cell = parts[1]
        
        # Handle view
        if len(parts) == 3:
            self.view = parts[2]
        else:
            if default_view is None:
                raise ValueError("No view specified and no default_view provided.")
            self.view = default_view
                
        # Try to detect if we're being called from within a cellview
        self.scriptInfo = self._detect_cellview_context()
        
        # print(self.scriptInfo)

        # Replace "_" with values from scriptInfo if available
        if self.scriptInfo:
            if self.lib == "_":
                self.lib = self.scriptInfo["LIB"]
            if self.cell == "_":
                self.cell = self.scriptInfo["CELL"]
            if self.view == "_":
                self.view = self.scriptInfo["VIEW"]

        self.isXschem=isXschem(self.lib)
        # Get library path from cds.lib
        lib_paths = parse_cdslib()
        if self.lib not in lib_paths:
            raise ValueError(f"Library '{self.lib}' not found in cds.lib")
        
        # Set up paths
        self.libPath = lib_paths[self.lib]
        
        if self.isXschem:
            if self.view in ['sch','sym','va']:
                self.cellPath=str(self.libPath)
                self.viewPath=str(self.libPath)
                self.viewfile=f'{self.libPath}/{self.cell}.{self.view}'
            else:
                self.cellPath=f'{self.libPath}/xschemviews/{self.cell}'
                self.viewPath=f'{self.cellPath}'
                viewD=getXschemCellViews(self.lib, self.cell)
                self.viewfile=viewD.get(self.view,None)
        else:
            self.cellPath = f"{self.libPath}/{self.cell}"
            self.viewPath = f"{self.cellPath}/{self.view}"
            
            # Read master.tag to get viewfile
            master_tag = f"{self.viewPath}/master.tag"
            try:
                with open(master_tag, 'r') as f:
                    # Skip first line (header)
                    next(f)
                    # Get first non-empty line after header
                    for line in f:
                        line = line.strip()
                        if line:
                            self.viewfile = f"{self.viewPath}/{line}"
                            break
                    else:
                        self.viewfile = None  # No viewfile found
            except FileNotFoundError:
                self.viewfile = None  # No master.tag found
            except Exception as e:
                raise ValueError(f"Error reading master.tag: {str(e)}")

        # Verify no empty components
        if not self.lib:
            raise ValueError("Library name cannot be empty")
        if not self.cell:
            raise ValueError("Cell name cannot be empty")
        if not self.view:
            raise ValueError("View name cannot be empty")

    def _detect_cellview_context(self) -> Optional[Dict[str, str]]:
        """
        Detect if this class is being instantiated from within a Cadence cellview.
        Returns dictionary with LIB, CELL, VIEW if found, None otherwise.
        """
        # Get the library paths from cds.lib
        lib_paths = parse_cdslib()
        
        # Get the call stack
        stack = inspect.stack()
        
        # Examine each frame in the stack
        for frame in stack:
            try:
                # Get the full path of the Python file
                filepath = Path(frame.filename).resolve()
                
                # Skip if it's not a file (e.g., interactive console)
                if not filepath.is_file():
                    continue
                
                # Get the parent directories
                parts = list(filepath.parents)
                
                # We need at least 3 levels: script.py, view, cell, lib_path
                if len(parts) < 3:
                    continue
                
                # The script should be in a view directory
                view_dir = parts[0]
                # Cell directory is one up
                cell_dir = parts[1]
                # Library directory is two up
                lib_dir = parts[2]
                
                # Check if this lib_dir matches any in our cds.lib
                for lib_name, lib_path in lib_paths.items():
                    if lib_dir == Path(lib_path):
                        # We found a match! This script is in a cellview
                        
                        isXsch=isXschem(lib_name)
                        
                        if isXsch:
                            return {
                                "LIB": lib_name,
                                "CELL": view_dir.name,
                                "VIEW": filepath.stem
                            }
                        else:
                            return {
                                "LIB": lib_name,
                                "CELL": cell_dir.name,
                                "VIEW": view_dir.name
                            }
            
            except (AttributeError, IndexError, TypeError):
                # Skip any frames that don't have the info we need
                continue
        
        # If we get here, we didn't find a matching cellview context
        return None

    def __str__(self):
        """String representation in library/cell/view format."""
        return f"{self.lib}/{self.cell}/{self.view}"

    def __repr__(self):
        """Detailed string representation."""
        return f"oalcv('{self.lib}/{self.cell}/{self.view}')"
        
    def exists(self) -> bool:
        """
        Check if the cellview exists by verifying viewfile exists.
        Returns False if viewfile is None or doesn't exist.
        """
        return self.viewfile is not None and os.path.exists(self.viewfile)
        
    def modDate(self) -> float | None:
        """
        Returns the modification timestamp of the viewfile.
        Returns None if the viewfile doesn't exist.
        """
        if not self.exists():
            return None
        return os.path.getmtime(self.viewfile)
        
    def read(self) -> str | None:
        """
        Reads the contents of the viewfile.
        Returns None if the viewfile doesn't exist.
        """
        if not self.exists():
            return None
        try:
            with open(self.viewfile, 'r') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Error reading viewfile {self.viewfile}: {str(e)}")
            
    def Import(self):
        if not self.exists():
            return None
        try:
            moduleName=f'{self.lib}.{self.cell}.{self.view}'
            spec = importlib.util.spec_from_file_location(moduleName, self.viewfile)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            raise ValueError(f"Error importing viewfile {self.viewfile}: {str(e)}")
        
            
            
    def write(self, content: str, viewfile: str | None = None) -> None:
        """
        Writes content to the viewfile.
        
        Args:
            content: String content to write
            viewfile: Optional viewfile name. Required if no viewfile exists yet.
            
        Raises:
            ValueError: If viewfile doesn't match existing viewfile,
                      or if no viewfile exists and none provided
        """
        assert not self.isXschem, "writing XSchem views not yet supported"
        # Case 1: We already have a viewfile
        if self.viewfile is not None:
            # If viewfile argument provided, it must match
            if viewfile is not None:
                expected_path = f"{self.viewPath}/{viewfile}"
                if self.viewfile != expected_path:
                    raise ValueError(
                        f"Provided viewfile '{viewfile}' doesn't match existing "
                        f"viewfile from master.tag: '{os.path.basename(self.viewfile)}'"
                    )
            
            # Write the content
            try:
                with open(self.viewfile, 'w') as f:
                    f.write(content)
            except Exception as e:
                raise ValueError(f"Error writing to viewfile {self.viewfile}: {str(e)}")
                
        # Case 2: No viewfile exists yet
        else:
            if viewfile is None:
                raise ValueError(
                    "No existing viewfile found in master.tag. "
                    "Must provide viewfile name for new cellview."
                )
                
            # Create view directory if it doesn't exist
            os.makedirs(self.viewPath, exist_ok=True)
            
            # Create master.tag
            try:
                with open(f"{self.viewPath}/master.tag", 'w') as f:
                    f.write("-- Master.tag File, Rev:1.0\n")
                    f.write(f"{viewfile}\n")
            except Exception as e:
                raise ValueError(f"Error creating master.tag: {str(e)}")
                
            # Set and create viewfile
            self.viewfile = f"{self.viewPath}/{viewfile}"
            try:
                with open(self.viewfile, 'w') as f:
                    f.write(content)
            except Exception as e:
                raise ValueError(f"Error writing to viewfile {self.viewfile}: {str(e)}")
                
    def writeText(self, content: str) -> None:
        """
        Writes content to a text viewfile.
        
        Args:
            content: String content to write
            
        Raises:
            ValueError: If existing viewfile is not a text view
        """
        self.write(content,'text.txt')
    