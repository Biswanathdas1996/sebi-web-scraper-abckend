"""
Example usage of the enhanced PDF processing with docling integration.

This example demonstrates how to use the enhanced PDF processor with 
both docling (when available) and fallback methods.
"""

from pathlib import Path
import json
from tool.fileReader.index import (
    process_test_enhanced_metadata_pdfs,
    test_single_pdf,
    extract_pdf_data,
    DOCLING_AVAILABLE
)

def main():
    """
    Example usage of enhanced PDF processing.
    """
    print("🚀 Enhanced PDF Processing with Docling Integration")
    print("=" * 60)
    print(f"Docling availability: {'✅ Available' if DOCLING_AVAILABLE else '❌ Not available'}")
    print()
    
    # Example 1: Process a single PDF file
    print("📄 Example 1: Processing a single PDF file")
    print("-" * 40)
    
    # Test with auto-detection (will use docling if available, fallback otherwise)
    result = test_single_pdf("page_1_1_1_Extension_of_timelin.pdf")
    
    if result:
        print(f"✅ Single PDF processing successful!")
        print(f"   Method used: {result.get('extraction_method', 'unknown')}")
        print(f"   Text length: {len(result.get('text', ''))}")
        print(f"   Tables found: {len(result.get('tables', []))}")
        
        # Show additional info for docling
        if result.get("extraction_method") == "docling":
            stats = result.get('processing_stats', {})
            print(f"   Pages processed: {stats.get('pages_processed', 0)}")
            print(f"   Sections found: {stats.get('sections_found', 0)}")
            
            if result.get('markdown'):
                print(f"   Markdown available: Yes ({len(result['markdown'])} chars)")
    
    print("\n" + "=" * 60)
    
    # Example 2: Process all PDFs in the test folder
    print("📁 Example 2: Processing all PDFs")
    print("-" * 40)
    
    # Process all PDFs with auto-detection
    result = process_test_enhanced_metadata_pdfs()
    
    if result:
        print(f"✅ Batch processing successful!")
        pdf_processing = result.get('pdf_processing', {})
        print(f"   Files processed: {pdf_processing.get('processed_files_count', 0)}")
        print(f"   Total files: {pdf_processing.get('total_pdf_files', 0)}")
        print(f"   Method: {pdf_processing.get('processing_method', 'unknown')}")
        
        # Show enhanced stats if available
        if 'processing_stats' in pdf_processing:
            stats = pdf_processing['processing_stats']
            print(f"   Successful: {stats.get('processed_successfully', 0)}")
            print(f"   Failed: {stats.get('failed_processing', 0)}")
            if DOCLING_AVAILABLE:
                print(f"   Docling successes: {stats.get('docling_successes', 0)}")
                print(f"   Fallback used: {stats.get('fallback_used', 0)}")
    
    print("\n" + "=" * 60)
    
    # Example 3: Direct API usage
    print("🔧 Example 3: Direct API usage")
    print("-" * 40)
    
    # Process a single file with specific method
    pdf_path = Path.cwd() / "test_enhanced_metadata" / "page_1_2_1_Use_of_liquid_mutual.pdf"
    
    if pdf_path.exists():
        # Try with docling if available
        result_docling = extract_pdf_data(str(pdf_path), use_docling=True)
        print(f"   Docling result: {result_docling.get('extraction_method', 'failed')}")
        
        # Try with standard methods
        result_standard = extract_pdf_data(str(pdf_path), use_docling=False)
        print(f"   Standard result: {result_standard.get('extraction_method', 'failed')}")
        
        # Compare results
        if result_docling.get('text') and result_standard.get('text'):
            docling_length = len(result_docling['text'])
            standard_length = len(result_standard['text'])
            print(f"   Text length comparison:")
            print(f"     Docling: {docling_length} chars")
            print(f"     Standard: {standard_length} chars")
            print(f"     Difference: {abs(docling_length - standard_length)} chars")
    
    print("\n🎉 Examples completed!")


def demonstrate_docling_features():
    """
    Demonstrate specific docling features when available.
    """
    if not DOCLING_AVAILABLE:
        print("⚠️  Docling not available - skipping feature demonstration")
        return
    
    print("🚀 Docling Feature Demonstration")
    print("=" * 40)
    
    from tool.fileReader.docling_processor import DoclingPDFProcessor
    
    # Initialize processor
    processor = DoclingPDFProcessor()
    
    # Process a sample PDF
    pdf_path = Path.cwd() / "test_enhanced_metadata" / "page_1_1_1_Extension_of_timelin.pdf"
    
    if pdf_path.exists():
        result = processor.extract_document_content(str(pdf_path))
        
        if "error" not in result:
            print("✅ Docling processing successful!")
            
            # Show markdown output
            if result.get('markdown'):
                print("\n📝 Markdown Output Sample:")
                print("-" * 30)
                print(result['markdown'][:500] + "...")
            
            # Show document structure
            structure = result.get('structure', {})
            if structure.get('headings'):
                print("\n🏗️  Document Structure:")
                print("-" * 30)
                for i, heading in enumerate(structure['headings'][:5]):
                    level = "  " * (heading.get('level', 1) - 1)
                    print(f"{level}- {heading.get('text', '')}")
            
            # Show processing stats
            stats = result.get('processing_stats', {})
            print(f"\n📊 Processing Statistics:")
            print("-" * 30)
            for key, value in stats.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
        else:
            print(f"❌ Docling processing failed: {result['error']}")
    else:
        print(f"❌ Sample PDF not found: {pdf_path}")


if __name__ == "__main__":
    # Run main examples
    main()
    
    print("\n" + "=" * 60)
    
    # Demonstrate docling-specific features
    demonstrate_docling_features()
