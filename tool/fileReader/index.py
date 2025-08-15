import os
import json
import PyPDF2
import pdfplumber
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

# LangSmith tracing
from langsmith import traceable


def extract_text_from_pdf_pypdf2(pdf_path: str) -> str:
    """
    Extract text from PDF using PyPDF2.
    Better for simple text extraction.
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"❌ PyPDF2 extraction failed for {pdf_path}: {e}")
        return ""


def extract_text_from_pdf_pdfplumber(pdf_path: str) -> Dict[str, Any]:
    """
    Extract text from PDF using pdfplumber.
    Better for structured data and tables.
    """
    try:
        extracted_data = {
            "text": "",
            "tables": [],
            "metadata": {}
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            # Extract metadata
            if pdf.metadata:
                extracted_data["metadata"] = {
                    "title": pdf.metadata.get("Title", ""),
                    "author": pdf.metadata.get("Author", ""),
                    "subject": pdf.metadata.get("Subject", ""),
                    "creator": pdf.metadata.get("Creator", ""),
                    "creation_date": str(pdf.metadata.get("CreationDate", "")),
                    "modification_date": str(pdf.metadata.get("ModDate", "")),
                    "pages": len(pdf.pages)
                }
            
            # Extract text from all pages
            full_text = ""
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    full_text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
                
                # Extract tables from page
                tables = page.extract_tables()
                if tables:
                    for table_num, table in enumerate(tables):
                        extracted_data["tables"].append({
                            "page": page_num + 1,
                            "table_number": table_num + 1,
                            "data": table
                        })
            
            extracted_data["text"] = full_text.strip()
        
        return extracted_data
    except Exception as e:
        print(f"❌ pdfplumber extraction failed for {pdf_path}: {e}")
        return {"text": "", "tables": [], "metadata": {}}


def extract_pdf_data(pdf_path: str, use_advanced_extraction: bool = True) -> Dict[str, Any]:
    """
    Extract comprehensive data from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        use_advanced_extraction: If True, use pdfplumber for better extraction
    
    Returns:
        Dictionary with extracted text, tables, and metadata
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        return {
            "error": f"PDF file not found: {pdf_path}",
            "text": "",
            "tables": [],
            "metadata": {},
            "file_info": {}
        }
    
    # Get file information
    file_info = {
        "filename": pdf_path.name,
        "full_path": str(pdf_path.absolute()),
        "file_size": pdf_path.stat().st_size,
        "last_modified": datetime.fromtimestamp(pdf_path.stat().st_mtime).isoformat(),
        "extraction_timestamp": datetime.now().isoformat()
    }
    
    if use_advanced_extraction:
        # Use pdfplumber for comprehensive extraction
        extracted_data = extract_text_from_pdf_pdfplumber(str(pdf_path))
        extracted_data["file_info"] = file_info
        extracted_data["extraction_method"] = "pdfplumber"
    else:
        # Use PyPDF2 for simple extraction
        text = extract_text_from_pdf_pypdf2(str(pdf_path))
        extracted_data = {
            "text": text,
            "tables": [],
            "metadata": {},
            "file_info": file_info,
            "extraction_method": "PyPDF2"
        }
    
    return extracted_data


def process_pdfs_from_folder(folder_path: str, metadata_json_path: str) -> Dict[str, Any]:
    """
    Process all PDFs from a folder and update the metadata JSON file with extracted data.
    
    Args:
        folder_path: Path to the folder containing PDFs
        metadata_json_path: Path to the scraping_metadata.json file
    
    Returns:
        Updated metadata with extracted PDF content
    """
    folder_path = Path(folder_path)
    metadata_path = Path(metadata_json_path)
    
    if not folder_path.exists():
        return {"error": f"Folder not found: {folder_path}"}
    
    if not metadata_path.exists():
        return {"error": f"Metadata JSON file not found: {metadata_path}"}
    
    # Load existing metadata
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load metadata JSON: {e}"}
    
    # Process each PDF file
    processed_count = 0
    pdf_files = list(folder_path.glob("*.pdf"))
    
    print(f"📁 Processing {len(pdf_files)} PDF files from {folder_path}")
    print(f"📄 Metadata file: {metadata_path}")
    
    for pdf_file in pdf_files:
        print(f"\n🔄 Processing: {pdf_file.name}")
        
        # Extract PDF data
        extracted_data = extract_pdf_data(str(pdf_file), use_advanced_extraction=True)
        
        if "error" in extracted_data:
            print(f"❌ Failed to process {pdf_file.name}: {extracted_data['error']}")
            continue
        
        # Find corresponding entry in metadata and update it
        updated = False
        
        # Check in page_results -> files array
        if "page_results" in metadata:
            for page_result in metadata["page_results"]:
                if isinstance(page_result, dict) and "files" in page_result:
                    for file_entry in page_result["files"]:
                        if isinstance(file_entry, dict):
                            # Check multiple possible filename fields
                            filename_fields = [
                                file_entry.get("original_filename", ""),
                                file_entry.get("downloaded_filename", ""),
                                Path(file_entry.get("file_path", "")).name
                            ]
                            
                            if pdf_file.name in filename_fields:
                                file_entry["extracted_content"] = extracted_data
                                updated = True
                                print(f"✅ Updated metadata for {pdf_file.name}")
                                break
                
                if updated:
                    break
        
        # Also check in all_files array if it exists
        if not updated and "all_files" in metadata:
            for file_entry in metadata["all_files"]:
                if isinstance(file_entry, dict):
                    # Check multiple possible filename fields
                    filename_fields = [
                        file_entry.get("original_filename", ""),
                        file_entry.get("downloaded_filename", ""),
                        Path(file_entry.get("file_path", "")).name
                    ]
                    
                    if pdf_file.name in filename_fields:
                        file_entry["extracted_content"] = extracted_data
                        updated = True
                        print(f"✅ Updated metadata for {pdf_file.name} in all_files")
                        break
        
        if updated:
            processed_count += 1
        else:
            print(f"⚠️  Could not find metadata entry for {pdf_file.name}")
    
    # Add processing summary to metadata
    metadata["pdf_processing"] = {
        "processing_timestamp": datetime.now().isoformat(),
        "processed_files_count": processed_count,
        "total_pdf_files": len(pdf_files),
        "processing_method": "pdfplumber + PyPDF2 fallback"
    }
    
    # Save updated metadata
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Successfully updated metadata file with {processed_count} processed PDFs")
        return metadata
    except Exception as e:
        return {"error": f"Failed to save updated metadata: {e}"}


def extract_text_summary(text: str, max_length: int = 500) -> str:
    """
    Create a summary of extracted text.
    """
    if not text or len(text) <= max_length:
        return text
    
    # Try to cut at sentence boundaries
    sentences = re.split(r'[.!?]+', text[:max_length * 2])
    summary = ""
    for sentence in sentences:
        if len(summary + sentence) <= max_length:
            summary += sentence + ". "
        else:
            break
    
    return summary.strip() + "..." if summary else text[:max_length] + "..."


@traceable(name="process_test_enhanced_metadata_pdfs", metadata={"tool": "pdf_text_extractor"})
def process_test_enhanced_metadata_pdfs():
    """
    Main function to process PDFs from test_enhanced_metadata folder
    and update scraping_metadata.json file.
    """
    # Get current working directory and construct paths using pathlib for cross-platform compatibility
    current_dir = Path.cwd()
    test_folder = current_dir / "test_enhanced_metadata"
    metadata_file = current_dir / "output/scraping_metadata.json"
    
    print("🚀 Starting PDF processing for SEBI documents...")
    print(f"📁 PDF folder: {test_folder}")
    print(f"📄 Metadata file: {metadata_file}")
    
    # Validate paths
    if not test_folder.exists():
        print(f"❌ Error: PDF folder not found at {test_folder}")
        return None
    
    if not metadata_file.exists():
        print(f"❌ Error: Metadata file not found at {metadata_file}")
        return None
    
    # Process PDFs
    result = process_pdfs_from_folder(str(test_folder), str(metadata_file))
    
    if "error" in result:
        print(f"❌ Processing failed: {result['error']}")
        return None
    
    print(f"\n🎉 PDF processing completed successfully!")
    print(f"📊 Processed {result['pdf_processing']['processed_files_count']} out of {result['pdf_processing']['total_pdf_files']} PDF files")
    
    return result


def refactor_metadata_paths(metadata_json_path: str) -> Dict[str, Any]:
    """
    Refactor the metadata JSON file to fix path mapping issues.
    
    Args:
        metadata_json_path: Path to the scraping_metadata.json file
    
    Returns:
        Dictionary with refactored metadata containing proper path mappings
    """
    metadata_path = Path(metadata_json_path)
    
    if not metadata_path.exists():
        return {"error": f"Metadata JSON file not found: {metadata_path}"}
    
    # Load existing metadata
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load metadata JSON: {e}"}
    
    print("🔧 Refactoring metadata for path mapping issues...")
    
    # Fix download_path to use relative paths
    if "download_path" in metadata:
        # Convert absolute path to relative path
        abs_path = Path(metadata["download_path"])
        if abs_path.is_absolute():
            # Make it relative to current directory
            metadata["download_path"] = "test_enhanced_metadata"
            print(f"✅ Fixed main download_path: {abs_path} -> test_enhanced_metadata")
    
    # Fix paths in page_results
    if "page_results" in metadata:
        for page_result in metadata["page_results"]:
            if isinstance(page_result, dict):
                # Fix download_path in page results
                if "download_path" in page_result:
                    abs_path = Path(page_result["download_path"])
                    if abs_path.is_absolute():
                        page_result["download_path"] = "test_enhanced_metadata"
                        print(f"✅ Fixed page result download_path")
                
                # Fix file paths in files array
                if "files" in page_result:
                    for file_entry in page_result["files"]:
                        if isinstance(file_entry, dict) and "file_path" in file_entry:
                            # Convert Windows backslashes to forward slashes for cross-platform compatibility
                            old_path = file_entry["file_path"]
                            # Convert to Path object and back to string with forward slashes
                            path_obj = Path(old_path)
                            if path_obj.is_absolute():
                                # Make relative to current directory
                                file_entry["file_path"] = str(Path("test_enhanced_metadata") / path_obj.name)
                            else:
                                # Just normalize the path separators
                                file_entry["file_path"] = str(path_obj).replace("\\", "/")
                            
                            if old_path != file_entry["file_path"]:
                                print(f"✅ Fixed file path: {old_path} -> {file_entry['file_path']}")
                
                # Fix file_paths array
                if "file_paths" in page_result:
                    fixed_paths = []
                    for old_path in page_result["file_paths"]:
                        path_obj = Path(old_path)
                        if path_obj.is_absolute():
                            # Make relative to current directory
                            new_path = str(Path("test_enhanced_metadata") / path_obj.name)
                        else:
                            # Just normalize the path separators
                            new_path = str(path_obj).replace("\\", "/")
                        fixed_paths.append(new_path)
                    
                    page_result["file_paths"] = fixed_paths
                    print(f"✅ Fixed {len(fixed_paths)} file paths in file_paths array")
    
    # Fix paths in all_files array
    if "all_files" in metadata:
        for file_entry in metadata["all_files"]:
            if isinstance(file_entry, dict) and "file_path" in file_entry:
                old_path = file_entry["file_path"]
                path_obj = Path(old_path)
                if path_obj.is_absolute():
                    # Make relative to current directory
                    file_entry["file_path"] = str(Path("test_enhanced_metadata") / path_obj.name)
                else:
                    # Just normalize the path separators
                    file_entry["file_path"] = str(path_obj).replace("\\", "/")
                
                if old_path != file_entry["file_path"]:
                    print(f"✅ Fixed all_files path: {old_path} -> {file_entry['file_path']}")
    
    # Fix paths in all_file_paths array
    if "all_file_paths" in metadata:
        fixed_paths = []
        for old_path in metadata["all_file_paths"]:
            path_obj = Path(old_path)
            if path_obj.is_absolute():
                # Make relative to current directory
                new_path = str(Path("test_enhanced_metadata") / path_obj.name)
            else:
                # Just normalize the path separators
                new_path = str(path_obj).replace("\\", "/")
            fixed_paths.append(new_path)
        
        metadata["all_file_paths"] = fixed_paths
        print(f"✅ Fixed {len(fixed_paths)} paths in all_file_paths array")
    
    # Add refactoring metadata
    metadata["path_refactoring"] = {
        "refactoring_timestamp": datetime.now().isoformat(),
        "changes_made": [
            "Converted absolute paths to relative paths",
            "Normalized path separators for cross-platform compatibility",
            "Updated download_path references",
            "Fixed file_path entries in all relevant arrays"
        ],
        "path_format": "Relative paths with forward slashes"
    }
    
    # Save refactored metadata
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Successfully refactored metadata file with proper path mappings")
        return metadata
    except Exception as e:
        return {"error": f"Failed to save refactored metadata: {e}"}


def validate_pdf_paths(metadata_json_path: str) -> Dict[str, Any]:
    """
    Validate that all PDF file paths in the metadata actually exist.
    
    Args:
        metadata_json_path: Path to the scraping_metadata.json file
    
    Returns:
        Dictionary with validation results
    """
    metadata_path = Path(metadata_json_path)
    
    if not metadata_path.exists():
        return {"error": f"Metadata JSON file not found: {metadata_path}"}
    
    # Load existing metadata
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load metadata JSON: {e}"}
    
    print("🔍 Validating PDF file paths...")
    
    validation_results = {
        "existing_files": [],
        "missing_files": [],
        "total_paths_checked": 0,
        "validation_timestamp": datetime.now().isoformat()
    }
    
    # Get current directory for relative path resolution
    current_dir = Path.cwd()
    
    # Check all_file_paths
    if "all_file_paths" in metadata:
        for file_path in metadata["all_file_paths"]:
            validation_results["total_paths_checked"] += 1
            
            # Resolve relative path
            full_path = current_dir / file_path
            
            if full_path.exists():
                validation_results["existing_files"].append(file_path)
                print(f"✅ Found: {file_path}")
            else:
                validation_results["missing_files"].append(file_path)
                print(f"❌ Missing: {file_path}")
    
    # Summary
    existing_count = len(validation_results["existing_files"])
    missing_count = len(validation_results["missing_files"])
    total_count = validation_results["total_paths_checked"]
    
    validation_results["summary"] = {
        "existing_files_count": existing_count,
        "missing_files_count": missing_count,
        "total_files_count": total_count,
        "success_rate": f"{(existing_count/total_count*100):.1f}%" if total_count > 0 else "0%"
    }
    
    print(f"\n📊 Validation Summary:")
    print(f"   ✅ Existing files: {existing_count}")
    print(f"   ❌ Missing files: {missing_count}")
    print(f"   📈 Success rate: {validation_results['summary']['success_rate']}")
    
    return validation_results


# Convenience function for quick testing
def test_single_pdf(pdf_filename: str):
    """
    Test extraction on a single PDF file from the test_enhanced_metadata folder.
    """
    current_dir = Path.cwd()
    pdf_path = current_dir / "test_enhanced_metadata" / pdf_filename
    
    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    
    print(f"🔍 Testing extraction on: {pdf_filename}")
    result = extract_pdf_data(str(pdf_path))
    
    if "error" in result:
        print(f"❌ Extraction failed: {result['error']}")
        return None
    
    print(f"✅ Extraction successful!")
    print(f"📄 Text length: {len(result['text'])} characters")
    print(f"📋 Tables found: {len(result['tables'])}")
    print(f"📑 Metadata fields: {len(result['metadata'])}")
    
    # Show first 200 characters of text
    if result['text']:
        print(f"\n📖 Text preview:\n{result['text'][:200]}...")
    
    return result


if __name__ == "__main__":
    # Check if user wants to refactor metadata paths
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--refactor-paths":
        print("🔧 Refactoring metadata for path mapping issues...")
        current_dir = Path.cwd()
        metadata_file = current_dir / "output/scraping_metadata.json"
        result = refactor_metadata_paths(str(metadata_file))
        
        if "error" in result:
            print(f"❌ Refactoring failed: {result['error']}")
        else:
            print("🎉 Path refactoring completed successfully!")
            
            # Also run validation
            print("\n" + "="*50)
            validation_result = validate_pdf_paths(str(metadata_file))
            if "error" not in validation_result:
                print("🔍 Path validation completed!")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "--validate-paths":
        print("🔍 Validating PDF file paths...")
        current_dir = Path.cwd()
        metadata_file = current_dir / "output/scraping_metadata.json"
        result = validate_pdf_paths(str(metadata_file))
        
        if "error" in result:
            print(f"❌ Validation failed: {result['error']}")
        else:
            print("🔍 Path validation completed!")
    
    else:
        # Run the main processing function
        process_test_enhanced_metadata_pdfs()