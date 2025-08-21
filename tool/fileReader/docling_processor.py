import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

# Docling imports for advanced document processing
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

# LangSmith tracing
from langsmith import traceable

class DoclingPDFProcessor:
    """
    Advanced PDF processor using docling for efficient document processing.
    """
    
    def __init__(self):
        """Initialize the docling processor with optimized settings."""
        try:
            # Try with basic configuration first
            self.converter = DocumentConverter()
            print("✅ Docling processor initialized with basic configuration")
        except Exception as e:
            # Handle Windows-specific symlink issues
            if "symlink" in str(e).lower() or "privilege" in str(e).lower():
                print(f"⚠️  Windows symlink permission issue detected: {e}")
                print("💡 Tip: Run as Administrator or enable Developer Mode for full docling features")
                print("🔄 Continuing with fallback initialization...")
                try:
                    # Try alternative initialization
                    import os
                    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
                    self.converter = DocumentConverter()
                    print("✅ Docling processor initialized with symlink workaround")
                except Exception as e2:
                    print(f"❌ Docling initialization failed completely: {e2}")
                    self.converter = None
            else:
                print(f"⚠️  Error initializing docling processor: {e}")
                self.converter = None
        
    def extract_document_content(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive content from PDF using docling.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with extracted content, structure, and metadata
        """
        try:
            pdf_path = Path(pdf_path)
            
            if not pdf_path.exists():
                return {
                    "error": f"PDF file not found: {pdf_path}",
                    "text": "",
                    "tables": [],
                    "structure": {},
                    "metadata": {}
                }
            
            if not self.converter:
                return {
                    "error": "Docling converter not initialized",
                    "text": "",
                    "tables": [],
                    "structure": {},
                    "metadata": {}
                }
            
            # Convert document using docling
            result = self.converter.convert(str(pdf_path))
            
            # Extract document data
            document = result.document
            
            # Get file information
            file_info = {
                "filename": pdf_path.name,
                "full_path": str(pdf_path.absolute()),
                "file_size": pdf_path.stat().st_size,
                "last_modified": datetime.fromtimestamp(pdf_path.stat().st_mtime).isoformat(),
                "extraction_timestamp": datetime.now().isoformat()
            }
            
            # Extract basic content
            text_content = document.export_to_text() if hasattr(document, 'export_to_text') else ""
            markdown_content = document.export_to_markdown() if hasattr(document, 'export_to_markdown') else ""
            
            # Extract structured content
            extracted_data = {
                "text": text_content,
                "markdown": markdown_content,
                "structure": self._extract_document_structure(document),
                "tables": self._extract_tables(document),
                "metadata": self._extract_metadata(document),
                "file_info": file_info,
                "extraction_method": "docling",
                "processing_stats": {
                    "pages_processed": getattr(document, 'page_count', 0) or len(getattr(document, 'pages', [])),
                    "characters_extracted": len(text_content),
                    "tables_found": len(self._extract_tables(document)),
                    "sections_found": len(self._extract_document_structure(document).get("sections", []))
                }
            }
            
            return extracted_data
            
        except Exception as e:
            return {
                "error": f"Docling extraction failed for {pdf_path}: {str(e)}",
                "text": "",
                "tables": [],
                "structure": {},
                "metadata": {},
                "file_info": {},
                "extraction_method": "docling_failed"
            }
    
    def _extract_document_structure(self, document) -> Dict[str, Any]:
        """Extract document structure including headings, sections, and hierarchy."""
        structure = {
            "sections": [],
            "headings": [],
            "hierarchy": []
        }
        
        try:
            # Extract document elements and their structure
            for item in document.iterate_items():
                if hasattr(item, 'label'):
                    if 'title' in str(item.label).lower() or 'heading' in str(item.label).lower():
                        structure["headings"].append({
                            "text": str(item.text) if hasattr(item, 'text') else str(item),
                            "level": self._determine_heading_level(item),
                            "type": str(item.label)
                        })
                    elif 'section' in str(item.label).lower():
                        structure["sections"].append({
                            "text": str(item.text) if hasattr(item, 'text') else str(item),
                            "type": str(item.label)
                        })
            
            # Build hierarchy from headings
            structure["hierarchy"] = self._build_hierarchy(structure["headings"])
            
        except Exception as e:
            print(f"Warning: Could not extract full document structure: {e}")
        
        return structure
    
    def _extract_tables(self, document) -> List[Dict[str, Any]]:
        """Extract tables with enhanced structure and metadata."""
        tables = []
        
        try:
            table_count = 0
            for item in document.iterate_items():
                if hasattr(item, 'label') and 'table' in str(item.label).lower():
                    table_count += 1
                    
                    # Extract table data
                    table_data = {
                        "table_number": table_count,
                        "type": str(item.label) if hasattr(item, 'label') else "table",
                        "text": str(item.text) if hasattr(item, 'text') else "",
                        "structure": {},
                        "metadata": {}
                    }
                    
                    # Try to extract structured table data if available
                    if hasattr(item, 'data') and item.data:
                        table_data["structure"] = item.data
                    
                    tables.append(table_data)
                    
        except Exception as e:
            print(f"Warning: Could not extract all tables: {e}")
        
        return tables
    
    def _extract_metadata(self, document) -> Dict[str, Any]:
        """Extract document metadata and properties."""
        metadata = {}
        
        try:
            # Extract basic document metadata
            if hasattr(document, 'metadata') and document.metadata:
                metadata.update(document.metadata)
            
            # Extract additional properties
            if hasattr(document, 'pages'):
                metadata["page_count"] = len(document.pages)
            
            # Extract document properties
            metadata["document_type"] = "PDF"
            metadata["processing_engine"] = "docling"
            
        except Exception as e:
            print(f"Warning: Could not extract full metadata: {e}")
        
        return metadata
    
    def _determine_heading_level(self, item) -> int:
        """Determine heading level based on item properties."""
        try:
            # This is a simplified heuristic - you might want to enhance this
            # based on font size, formatting, or other properties available in docling
            label = str(item.label).lower()
            if 'h1' in label or 'title' in label:
                return 1
            elif 'h2' in label or 'subtitle' in label:
                return 2
            elif 'h3' in label:
                return 3
            else:
                return 4
        except:
            return 4
    
    def _build_hierarchy(self, headings: List[Dict]) -> List[Dict]:
        """Build hierarchical structure from headings."""
        hierarchy = []
        stack = []
        
        for heading in headings:
            level = heading["level"]
            
            # Pop items from stack until we find the parent level
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            
            # Create hierarchy item
            hierarchy_item = {
                "text": heading["text"],
                "level": level,
                "children": []
            }
            
            # Add to parent's children if there's a parent
            if stack:
                stack[-1]["children"].append(hierarchy_item)
            else:
                hierarchy.append(hierarchy_item)
            
            stack.append(hierarchy_item)
        
        return hierarchy


class EnhancedPDFProcessor:
    """
    Enhanced PDF processor that combines docling with fallback methods.
    """
    
    def __init__(self, use_docling: bool = True):
        """Initialize with option to use docling or fallback methods."""
        self.use_docling = use_docling
        if use_docling:
            try:
                self.docling_processor = DoclingPDFProcessor()
                print("✅ Docling processor initialized successfully")
            except Exception as e:
                print(f"⚠️  Docling initialization failed, using fallback: {e}")
                self.use_docling = False
                self.docling_processor = None
        else:
            self.docling_processor = None
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF with docling as primary method and fallback to other methods.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with extracted content and metadata
        """
        if self.use_docling and self.docling_processor:
            # Try docling first
            result = self.docling_processor.extract_document_content(pdf_path)
            
            if "error" not in result:
                print(f"✅ Successfully processed {Path(pdf_path).name} with docling")
                return result
            else:
                print(f"⚠️  Docling failed for {Path(pdf_path).name}, trying fallback methods")
        
        # Fallback to existing methods from the original code
        return self._fallback_extraction(pdf_path)
    
    def _fallback_extraction(self, pdf_path: str) -> Dict[str, Any]:
        """Fallback to original PyPDF2/pdfplumber extraction methods."""
        # Import the original functions (assuming they're available)
        try:
            from . import extract_pdf_data
            return extract_pdf_data(pdf_path, use_advanced_extraction=True)
        except ImportError:
            # If import fails, implement basic extraction here
            return {
                "error": "Both docling and fallback methods failed",
                "text": "",
                "tables": [],
                "structure": {},
                "metadata": {},
                "extraction_method": "fallback_failed"
            }


@traceable(name="process_pdfs_with_docling", metadata={"tool": "docling_pdf_processor"})
def process_pdfs_with_docling(folder_path: str, metadata_json_path: str, use_docling: bool = True) -> Dict[str, Any]:
    """
    Process all PDFs from a folder using docling and update the metadata JSON file.
    
    Args:
        folder_path: Path to the folder containing PDFs
        metadata_json_path: Path to the scraping_metadata.json file
        use_docling: Whether to use docling (True) or fallback methods (False)
    
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
    
    # Initialize enhanced processor
    processor = EnhancedPDFProcessor(use_docling=use_docling)
    
    # Process each PDF file
    processed_count = 0
    failed_count = 0
    pdf_files = list(folder_path.glob("*.pdf"))
    
    print(f"📁 Processing {len(pdf_files)} PDF files from {folder_path}")
    print(f"📄 Metadata file: {metadata_path}")
    print(f"🔧 Using {'docling' if use_docling else 'fallback methods'} for processing")
    
    processing_stats = {
        "total_files": len(pdf_files),
        "processed_successfully": 0,
        "failed_processing": 0,
        "docling_successes": 0,
        "fallback_used": 0,
        "processing_method": "docling" if use_docling else "fallback"
    }
    
    for pdf_file in pdf_files:
        print(f"\n🔄 Processing: {pdf_file.name}")
        
        # Extract PDF data using enhanced processor
        extracted_data = processor.process_pdf(str(pdf_file))
        
        if "error" in extracted_data:
            print(f"❌ Failed to process {pdf_file.name}: {extracted_data['error']}")
            failed_count += 1
            processing_stats["failed_processing"] += 1
            continue
        
        # Track processing method statistics
        if extracted_data.get("extraction_method") == "docling":
            processing_stats["docling_successes"] += 1
        else:
            processing_stats["fallback_used"] += 1
        
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
            processing_stats["processed_successfully"] += 1
        else:
            print(f"⚠️  Could not find metadata entry for {pdf_file.name}")
    
    # Add processing summary to metadata
    metadata["pdf_processing"] = {
        "processing_timestamp": datetime.now().isoformat(),
        "processed_files_count": processed_count,
        "failed_files_count": failed_count,
        "total_pdf_files": len(pdf_files),
        "processing_method": "enhanced_docling_processor",
        "docling_enabled": use_docling,
        "processing_stats": processing_stats
    }
    
    # Save updated metadata
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Successfully updated metadata file")
        print(f"📊 Processing Summary:")
        print(f"   ✅ Processed: {processed_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   🚀 Docling successes: {processing_stats['docling_successes']}")
        print(f"   🔄 Fallback used: {processing_stats['fallback_used']}")
        return metadata
    except Exception as e:
        return {"error": f"Failed to save updated metadata: {e}"}


@traceable(name="process_test_enhanced_metadata_with_docling", metadata={"tool": "docling_enhanced_processor"})
def process_test_enhanced_metadata_with_docling():
    """
    Main function to process PDFs from test_enhanced_metadata folder using docling.
    """
    # Get current working directory and construct paths
    current_dir = Path.cwd()
    test_folder = current_dir / "test_enhanced_metadata"
    metadata_file = current_dir / "output/scraping_metadata.json"
    
    print("🚀 Starting enhanced PDF processing with docling for SEBI documents...")
    print(f"📁 PDF folder: {test_folder}")
    print(f"📄 Metadata file: {metadata_file}")
    
    # Validate paths
    if not test_folder.exists():
        print(f"❌ Error: PDF folder not found at {test_folder}")
        return None
    
    if not metadata_file.exists():
        print(f"❌ Error: Metadata file not found at {metadata_file}")
        return None
    
    # Process PDFs with docling
    result = process_pdfs_with_docling(str(test_folder), str(metadata_file), use_docling=True)
    
    if "error" in result:
        print(f"❌ Processing failed: {result['error']}")
        return None
    
    print(f"\n🎉 Enhanced PDF processing completed successfully!")
    stats = result['pdf_processing']['processing_stats']
    print(f"📊 Final Statistics:")
    print(f"   📂 Total files: {stats['total_files']}")
    print(f"   ✅ Successfully processed: {stats['processed_successfully']}")
    print(f"   🚀 Docling successes: {stats['docling_successes']}")
    print(f"   🔄 Fallback used: {stats['fallback_used']}")
    print(f"   ❌ Failed: {stats['failed_processing']}")
    
    return result


# Test function for a single PDF with docling
def test_docling_on_single_pdf(pdf_filename: str):
    """
    Test docling extraction on a single PDF file from the test_enhanced_metadata folder.
    """
    # Go up two levels to reach the main directory, then into test_enhanced_metadata
    current_dir = Path.cwd()
    if current_dir.name == "fileReader":
        # If we're in the fileReader directory, go up two levels
        base_dir = current_dir.parent.parent
    else:
        # If we're in the main directory
        base_dir = current_dir
    
    pdf_path = base_dir / "test_enhanced_metadata" / pdf_filename
    
    print(f"🔍 Looking for PDF at: {pdf_path}")
    
    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    
    print(f"🔍 Testing docling extraction on: {pdf_filename}")
    
    # Initialize docling processor
    processor = DoclingPDFProcessor()
    result = processor.extract_document_content(str(pdf_path))
    
    if "error" in result:
        print(f"❌ Docling extraction failed: {result['error']}")
        return None
    
    print(f"✅ Docling extraction successful!")
    stats = result.get('processing_stats', {})
    print(f"📄 Text length: {stats.get('characters_extracted', 0)} characters")
    print(f"📋 Tables found: {stats.get('tables_found', 0)}")
    print(f"📑 Pages processed: {stats.get('pages_processed', 0)}")
    print(f"🏗️  Sections found: {stats.get('sections_found', 0)}")
    
    # Show text preview
    if result.get('text'):
        print(f"\n📖 Text preview:\n{result['text'][:300]}...")
    
    # Show markdown preview if available
    if result.get('markdown'):
        print(f"\n📝 Markdown preview:\n{result['markdown'][:300]}...")
    
    # Show structure preview
    structure = result.get('structure', {})
    if structure.get('headings'):
        print(f"\n🏗️  Document structure preview:")
        for heading in structure['headings'][:3]:  # Show first 3 headings
            print(f"   Level {heading.get('level', 0)}: {heading.get('text', '')}")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-single" and len(sys.argv) > 2:
            # Test single PDF
            pdf_filename = sys.argv[2]
            test_docling_on_single_pdf(pdf_filename)
        elif sys.argv[1] == "--fallback":
            # Use fallback methods only
            print("🔄 Running with fallback methods only...")
            current_dir = Path.cwd()
            test_folder = current_dir / "test_enhanced_metadata"
            metadata_file = current_dir / "output/scraping_metadata.json"
            result = process_pdfs_with_docling(str(test_folder), str(metadata_file), use_docling=False)
        else:
            print("Usage:")
            print("  python docling_processor.py                    # Process all PDFs with docling")
            print("  python docling_processor.py --test-single <filename>  # Test single PDF")
            print("  python docling_processor.py --fallback         # Use fallback methods only")
    else:
        # Run the main processing function with docling
        process_test_enhanced_metadata_with_docling()
