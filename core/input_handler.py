"""
Input handling system for AI Page Reordering Automation System
Supports PDF, PNG, JPG, TIFF files with batch processing
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import mimetypes
from PIL import Image
import PyPDF2
from pdf2image import convert_from_path
import tempfile
import shutil

class PageInfo:
    """Data class to store page information"""
    
    def __init__(self, file_path: str, page_number: int = 0, image: Optional[Image.Image] = None):
        self.file_path = Path(file_path)
        self.original_name = self.file_path.name
        self.page_number = page_number  # For multi-page documents like PDFs
        self.image = image
        self.metadata = {}
        self.processing_history = []
        
    def __str__(self):
        return f"PageInfo({self.original_name}, page={self.page_number})"
    
    def __repr__(self):
        return self.__str__()

class InputHandler:
    """Handles input file processing and validation"""
    
    # Support ALL common image formats
    SUPPORTED_IMAGE_FORMATS = {
        '.png', '.jpg', '.jpeg', '.jpe', '.jfif',  # JPEG variants
        '.tiff', '.tif',  # TIFF
        '.bmp', '.dib',  # Bitmap
        '.webp',  # WebP
        '.gif',  # GIF
        '.ico',  # Icon
        '.ppm', '.pgm', '.pbm', '.pnm',  # Netpbm
        '.pcx',  # PCX
        '.tga', '.icb', '.vda', '.vst',  # Targa
        '.jp2', '.j2k', '.jpf', '.jpx', '.jpm',  # JPEG 2000
        '.heic', '.heif'  # HEIF/HEIC (if supported by PIL)
    }
    SUPPORTED_DOCUMENT_FORMATS = {'.pdf'}
    
    def __init__(self, logger):
        self.logger = logger
        self.temp_dir = None
        self._setup_temp_directory()
    
    def _setup_temp_directory(self):
        """Create temporary directory for processing"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="page_reorder_"))
        self.logger.debug(f"Created temp directory: {self.temp_dir}")
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.logger.debug("Cleaned up temporary files")
    
    def __del__(self):
        """Ensure cleanup on destruction"""
        self.cleanup()
    
    def load_files(self, input_path: Union[str, Path]) -> List[PageInfo]:
        """
        Load files from input path (file or directory)
        Returns list of PageInfo objects
        """
        input_path = Path(input_path)
        pages = []
        
        if input_path.is_file():
            pages = self._load_single_file(input_path)
        elif input_path.is_dir():
            pages = self._load_directory(input_path)
        else:
            self.logger.error(f"Invalid input path: {input_path}")
            return []
        
        self.logger.info(f"Loaded {len(pages)} pages from {input_path}")
        return pages
    
    def _load_single_file(self, file_path: Path) -> List[PageInfo]:
        """Load a single file (PDF or image)"""
        pages = []
        file_ext = file_path.suffix.lower()
        
        if file_ext in self.SUPPORTED_DOCUMENT_FORMATS:
            pages = self._load_pdf(file_path)
        elif file_ext in self.SUPPORTED_IMAGE_FORMATS:
            page = self._load_image(file_path)
            if page:
                pages.append(page)
        else:
            self.logger.warning(f"Unsupported file format: {file_ext}")
        
        return pages
    
    def _load_directory(self, dir_path: Path) -> List[PageInfo]:
        """Load all supported files from directory"""
        pages = []
        
        # Get all files and sort them naturally
        files = []
        for file_path in dir_path.iterdir():
            if file_path.is_file() and self._is_supported_file(file_path):
                files.append(file_path)
        
        # Sort files naturally (handle numeric sorting)
        files.sort(key=self._natural_sort_key)
        
        # Load each file
        for file_path in files:
            file_pages = self._load_single_file(file_path)
            pages.extend(file_pages)
        
        return pages
    
    def _load_pdf(self, pdf_path: Path) -> List[PageInfo]:
        """Load pages from PDF file"""
        pages = []
        
        try:
            # First, try to get page count
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
            
            self.logger.debug(f"Converting PDF to images: {pdf_path} ({page_count} pages)")
            
            # Convert PDF to images
            images = convert_from_path(str(pdf_path), dpi=300, fmt='png')
            
            for i, image in enumerate(images):
                # Save temporary image
                temp_path = self.temp_dir / f"{pdf_path.stem}_page_{i+1:03d}.png"
                image.save(temp_path)
                
                # Create PageInfo
                page_info = PageInfo(str(temp_path), page_number=i+1, image=image)
                page_info.metadata = {
                    'source_pdf': str(pdf_path),
                    'pdf_page_number': i+1,
                    'total_pdf_pages': page_count,
                    'dpi': 300
                }
                pages.append(page_info)
            
            self.logger.debug(f"Extracted {len(pages)} pages from PDF")
            
        except Exception as e:
            self.logger.error(f"Failed to load PDF {pdf_path}: {str(e)}")
        
        return pages
    
    def _load_image(self, image_path: Path) -> Optional[PageInfo]:
        """Load single image file"""
        try:
            # Open and validate image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Create PageInfo
            page_info = PageInfo(str(image_path), page_number=0, image=image)
            page_info.metadata = {
                'original_format': image.format,
                'size': image.size,
                'mode': image.mode
            }
            
            self.logger.debug(f"Loaded image: {image_path} ({image.size})")
            return page_info
            
        except Exception as e:
            self.logger.error(f"Failed to load image {image_path}: {str(e)}")
            return None
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file format is supported"""
        ext = file_path.suffix.lower()
        return ext in (self.SUPPORTED_IMAGE_FORMATS | self.SUPPORTED_DOCUMENT_FORMATS)
    
    def _natural_sort_key(self, file_path: Path) -> tuple:
        """Generate sort key for natural sorting (handles numbers correctly)"""
        import re
        
        name = file_path.stem.lower()
        # Split into text and number parts
        parts = re.findall(r'(\d+|\D+)', name)
        
        # Convert number parts to integers for proper sorting
        key_parts = []
        for part in parts:
            if part.isdigit():
                key_parts.append(int(part))
            else:
                key_parts.append(part)
        
        return tuple(key_parts)
    
    def validate_input(self, input_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate input path and return information
        Returns dict with validation results
        """
        input_path = Path(input_path)
        result = {
            'is_valid': False,
            'exists': input_path.exists(),
            'is_file': False,
            'is_directory': False,
            'supported_files': [],
            'unsupported_files': [],
            'total_files': 0,
            'estimated_pages': 0,
            'errors': []
        }
        
        if not result['exists']:
            result['errors'].append(f"Path does not exist: {input_path}")
            return result
        
        if input_path.is_file():
            result['is_file'] = True
            if self._is_supported_file(input_path):
                result['supported_files'].append(str(input_path))
                result['total_files'] = 1
                # Estimate pages (PDF might have multiple, images have 1)
                if input_path.suffix.lower() == '.pdf':
                    try:
                        with open(input_path, 'rb') as file:
                            pdf_reader = PyPDF2.PdfReader(file)
                            result['estimated_pages'] = len(pdf_reader.pages)
                    except:
                        result['estimated_pages'] = 1
                else:
                    result['estimated_pages'] = 1
                result['is_valid'] = True
            else:
                result['unsupported_files'].append(str(input_path))
                result['errors'].append(f"Unsupported file format: {input_path.suffix}")
        
        elif input_path.is_directory():
            result['is_directory'] = True
            for file_path in input_path.iterdir():
                if file_path.is_file():
                    result['total_files'] += 1
                    if self._is_supported_file(file_path):
                        result['supported_files'].append(str(file_path))
                        # Each image is 1 page, PDFs might be multiple
                        if file_path.suffix.lower() == '.pdf':
                            try:
                                with open(file_path, 'rb') as file:
                                    pdf_reader = PyPDF2.PdfReader(file)
                                    result['estimated_pages'] += len(pdf_reader.pages)
                            except:
                                result['estimated_pages'] += 1
                        else:
                            result['estimated_pages'] += 1
                    else:
                        result['unsupported_files'].append(str(file_path))
            
            if result['supported_files']:
                result['is_valid'] = True
            else:
                result['errors'].append("No supported files found in directory")
        
        else:
            result['errors'].append(f"Path is neither file nor directory: {input_path}")
        
        return result
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed information about a file"""
        info = {
            'path': str(file_path),
            'name': file_path.name,
            'size': 0,
            'type': 'unknown',
            'mime_type': None,
            'is_supported': False,
            'estimated_pages': 0,
            'error': None
        }
        
        try:
            if file_path.exists():
                info['size'] = file_path.stat().st_size
                info['mime_type'] = mimetypes.guess_type(str(file_path))[0]
                
                ext = file_path.suffix.lower()
                if ext in self.SUPPORTED_IMAGE_FORMATS:
                    info['type'] = 'image'
                    info['is_supported'] = True
                    info['estimated_pages'] = 1
                elif ext in self.SUPPORTED_DOCUMENT_FORMATS:
                    info['type'] = 'document'
                    info['is_supported'] = True
                    # Try to get PDF page count
                    if ext == '.pdf':
                        try:
                            with open(file_path, 'rb') as file:
                                pdf_reader = PyPDF2.PdfReader(file)
                                info['estimated_pages'] = len(pdf_reader.pages)
                        except:
                            info['estimated_pages'] = 1
            else:
                info['error'] = "File does not exist"
                
        except Exception as e:
            info['error'] = str(e)
        
        return info
