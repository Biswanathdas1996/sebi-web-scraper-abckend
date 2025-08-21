"""
README: Docling Integration for Enhanced PDF Processing

## Overview

This integration adds docling support to your existing PDF processing workflow, providing enhanced document understanding capabilities including:

1. **Better Text Extraction**: More accurate text extraction compared to PyPDF2/pdfplumber
2. **Document Structure**: Automatic extraction of headings, sections, and document hierarchy
3. **Table Processing**: Advanced table detection and extraction
4. **Markdown Export**: Documents can be exported to markdown format
5. **OCR Support**: Built-in OCR for scanned documents

## Files Added/Modified

### New Files:

- `docling_processor.py`: Main docling integration with fallback support

### Modified Files:

- `index.py`: Enhanced with docling integration while maintaining backward compatibility

## Installation

The following packages have been installed:

```bash
pip install docling docling-core docling-ibm-models
```

## Usage Options

### 1. Automatic Detection (Recommended)

```bash
python index.py
```

- Automatically detects if docling is available
- Uses docling if available, falls back to standard methods if not

### 2. Force Docling Usage

```bash
python index.py --use-docling
```

- Forces use of docling (will fail if not properly installed)

### 3. Force Standard Methods

```bash
python index.py --no-docling
```

- Uses only PyPDF2/pdfplumber methods

### 4. Test Single PDF

```bash
# Test with standard methods
python index.py --test-single "filename.pdf"

# Test with docling
python index.py --test-single "filename.pdf" --docling
```

### 5. Standalone Docling Processor

```bash
# Process all PDFs with docling
python docling_processor.py

# Test single PDF with docling
python docling_processor.py --test-single "filename.pdf"

# Use fallback methods only
python docling_processor.py --fallback
```

## Features Comparison

| Feature            | PyPDF2 | pdfplumber | docling   |
| ------------------ | ------ | ---------- | --------- |
| Text Extraction    | Basic  | Good       | Excellent |
| Table Detection    | None   | Good       | Excellent |
| Document Structure | None   | Limited    | Excellent |
| OCR Support        | None   | None       | Yes       |
| Markdown Export    | None   | None       | Yes       |
| Scanned Documents  | Poor   | Poor       | Good      |
| Complex Layouts    | Poor   | Fair       | Excellent |

## Docling Output Structure

When docling is used successfully, the output includes additional fields:

```json
{
  "text": "Plain text content",
  "markdown": "Markdown formatted content",
  "structure": {
    "sections": [],
    "headings": [
      {
        "text": "Heading text",
        "level": 1,
        "type": "title"
      }
    ],
    "hierarchy": []
  },
  "tables": [
    {
      "table_number": 1,
      "type": "table",
      "structure": {},
      "metadata": {}
    }
  ],
  "processing_stats": {
    "pages_processed": 5,
    "characters_extracted": 12345,
    "tables_found": 3,
    "sections_found": 8
  },
  "extraction_method": "docling"
}
```

## Troubleshooting

### Windows Symlink Issues

If you encounter symlink errors on Windows:

1. Run PowerShell as Administrator
2. Enable Developer Mode in Windows Settings
3. Or use the `--no-docling` flag to use standard methods

### Model Download Issues

Docling may download AI models on first use:

- This is normal and happens once
- Requires internet connection
- Models are cached for future use

### Fallback Behavior

The integration is designed to gracefully fall back:

1. Try docling first (if available and requested)
2. Fall back to pdfplumber if docling fails
3. Fall back to PyPDF2 if pdfplumber fails
4. Always return a result structure

## Performance Notes

- **First Run**: Slower due to model downloads
- **Subsequent Runs**: Faster with cached models
- **Complex Documents**: docling excels with complex layouts
- **Simple Documents**: All methods perform similarly
- **Large Batches**: docling provides more consistent results

## Integration Benefits

1. **Backward Compatibility**: Existing code continues to work
2. **Graceful Degradation**: Falls back if docling unavailable
3. **Enhanced Output**: Better structure and metadata when available
4. **Configurable**: Can choose processing method per use case
5. **Traceable**: Includes langsmith tracing for all methods

## Next Steps

1. Test with your specific document types
2. Adjust pipeline options in `DoclingPDFProcessor` if needed
3. Consider batch processing for large document sets
4. Monitor processing statistics to optimize workflow
   """
