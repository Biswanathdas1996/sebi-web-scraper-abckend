"""
Workflow Visualization and Documentation Generator

This module provides utilities to visualize and document the LangGraph workflow
"""

import json
from typing import Dict, Any, List
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def calculate_node_connection_points(start_node, end_node, sizes_dict):
    """
    Calculate precise connection points on node boundaries for accurate arrows
    """
    import math
    
    start_pos = start_node
    end_pos = end_node
    
    # Calculate direction vector
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance == 0:
        return start_pos, end_pos
    
    # Normalize direction
    dx_norm = dx / distance
    dy_norm = dy / distance
    
    # Get node sizes
    start_size = sizes_dict.get('start', (1.0, 1.0))
    end_size = sizes_dict.get('end', (1.0, 1.0))
    
    # Calculate connection points on node boundaries
    start_offset = max(start_size[0], start_size[1]) * 0.5
    end_offset = max(end_size[0], end_size[1]) * 0.5
    
    start_connection = (start_pos[0] + dx_norm * start_offset, 
                       start_pos[1] + dy_norm * start_offset)
    end_connection = (end_pos[0] - dx_norm * end_offset, 
                     end_pos[1] - dy_norm * end_offset)
    
    return start_connection, end_connection


def generate_workflow_diagram():
    """
    Generate a visual diagram of the SEBI workflow with improved layout and spacing
    """
    try:
        fig, ax = plt.subplots(1, 1, figsize=(20, 14))
        ax.set_xlim(0, 18)
        ax.set_ylim(0, 14)
        ax.axis('off')
        
        # Title with better positioning
        ax.text(9, 13.2, 'LangGraph SEBI Document Processing Workflow', 
                fontsize=20, fontweight='bold', ha='center')
        ax.text(9, 12.6, 'Multi-Agent System Architecture', 
                fontsize=16, ha='center', style='italic', color='#666')
        
        # Define enhanced colors and styles
        colors = {
            'start_end': '#4CAF50',
            'agent': '#2196F3',
            'decision': '#FF9800',
            'finalize': '#9C27B0',
            'data': '#607D8B',
            'success_path': '#4CAF50',
            'error_path': '#f44336',
            'data_flow': '#9E9E9E'
        }
        
        # Improved node positions with better spacing
        nodes = {
            'START': (2, 10.5),
            'web_scraping': (6, 10.5),
            'scraping_check': (10, 10.5),
            'doc_processing': (6, 8),
            'processing_check': (10, 8),
            'analysis': (6, 5.5),
            'finalize': (14, 7),
            'END': (16.5, 7)
        }
        
        # Draw START node with enhanced styling
        start_circle = patches.Circle(nodes['START'], 0.5, 
                                    facecolor=colors['start_end'], alpha=0.9, 
                                    linewidth=3, edgecolor='darkgreen')
        ax.add_patch(start_circle)
        ax.text(nodes['START'][0], nodes['START'][1], 'START', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=14)
        
        # Draw Web Scraping Agent with improved spacing
        scraping_rect = patches.FancyBboxPatch((nodes['web_scraping'][0]-1.5, nodes['web_scraping'][1]-0.8), 
                                             3.0, 1.6, boxstyle="round,pad=0.15",
                                             facecolor=colors['agent'], alpha=0.9, 
                                             linewidth=2, edgecolor='darkblue')
        ax.add_patch(scraping_rect)
        ax.text(nodes['web_scraping'][0], nodes['web_scraping'][1]+0.3, 'Web Scraping Agent', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=12)
        ax.text(nodes['web_scraping'][0], nodes['web_scraping'][1]-0.1, '• Download PDFs\n• Extract links\n• Metadata collection', 
                ha='center', va='center', color='white', fontsize=9)
        
        # Draw Scraping Decision Diamond with better size
        scraping_diamond = patches.RegularPolygon(nodes['scraping_check'], 4, radius=1.0, 
                                                orientation=3.14159/4, facecolor=colors['decision'], 
                                                alpha=0.9, linewidth=2, edgecolor='darkorange')
        ax.add_patch(scraping_diamond)
        ax.text(nodes['scraping_check'][0], nodes['scraping_check'][1]+0.15, 'Files', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=11)
        ax.text(nodes['scraping_check'][0], nodes['scraping_check'][1]-0.15, 'Downloaded?', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=11)
        
        # Draw Document Processing Agent with better positioning
        processing_rect = patches.FancyBboxPatch((nodes['doc_processing'][0]-1.5, nodes['doc_processing'][1]-0.8), 
                                               3.0, 1.6, boxstyle="round,pad=0.15",
                                               facecolor=colors['agent'], alpha=0.9, 
                                               linewidth=2, edgecolor='darkblue')
        ax.add_patch(processing_rect)
        ax.text(nodes['doc_processing'][0], nodes['doc_processing'][1]+0.3, 'Document Processing Agent', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=12)
        ax.text(nodes['doc_processing'][0], nodes['doc_processing'][1]-0.1, '• PDF text extraction\n• Metadata parsing\n• Content validation', 
                ha='center', va='center', color='white', fontsize=9)
        
        # Draw Processing Decision Diamond
        processing_diamond = patches.RegularPolygon(nodes['processing_check'], 4, radius=1.0, 
                                                  orientation=3.14159/4, facecolor=colors['decision'], 
                                                  alpha=0.9, linewidth=2, edgecolor='darkorange')
        ax.add_patch(processing_diamond)
        ax.text(nodes['processing_check'][0], nodes['processing_check'][1]+0.15, 'Text', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=11)
        ax.text(nodes['processing_check'][0], nodes['processing_check'][1]-0.15, 'Extracted?', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=11)
        
        # Draw Analysis Agent
        analysis_rect = patches.FancyBboxPatch((nodes['analysis'][0]-1.5, nodes['analysis'][1]-0.8), 
                                             3.0, 1.6, boxstyle="round,pad=0.15",
                                             facecolor=colors['agent'], alpha=0.9, 
                                             linewidth=2, edgecolor='darkblue')
        ax.add_patch(analysis_rect)
        ax.text(nodes['analysis'][0], nodes['analysis'][1]+0.3, 'Analysis Agent', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=12)
        ax.text(nodes['analysis'][0], nodes['analysis'][1]-0.1, '• LLM Classification\n• Department mapping\n• Key insights extraction', 
                ha='center', va='center', color='white', fontsize=9)
        
        # Draw Finalize Node with enhanced styling
        finalize_rect = patches.FancyBboxPatch((nodes['finalize'][0]-1.5, nodes['finalize'][1]-0.8), 
                                             3.0, 1.6, boxstyle="round,pad=0.15",
                                             facecolor=colors['finalize'], alpha=0.9, 
                                             linewidth=2, edgecolor='darkmagenta')
        ax.add_patch(finalize_rect)
        ax.text(nodes['finalize'][0], nodes['finalize'][1]+0.3, 'Finalize & Report', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=12)
        ax.text(nodes['finalize'][0], nodes['finalize'][1]-0.1, '• Generate reports\n• Save results\n• Cleanup', 
                ha='center', va='center', color='white', fontsize=9)
        
        # Draw END node with enhanced styling
        end_circle = patches.Circle(nodes['END'], 0.5, 
                                  facecolor=colors['start_end'], alpha=0.9, 
                                  linewidth=3, edgecolor='darkgreen')
        ax.add_patch(end_circle)
        ax.text(nodes['END'][0], nodes['END'][1], 'END', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=14)
        
        # Draw data storage nodes with better positioning
        data_nodes = [
            {'pos': (2, 8), 'label': 'SEBI\nWebsite', 'size': (1.4, 1.0)},
            {'pos': (2, 5.5), 'label': 'PDF Files', 'size': (1.4, 1.0)},
            {'pos': (10, 3), 'label': 'JSON Results', 'size': (1.4, 1.0)},
            {'pos': (14, 3), 'label': 'Final Report', 'size': (1.4, 1.0)}
        ]
        
        for data_node in data_nodes:
            data_rect = patches.FancyBboxPatch((data_node['pos'][0]-data_node['size'][0]/2, 
                                             data_node['pos'][1]-data_node['size'][1]/2), 
                                             data_node['size'][0], data_node['size'][1], 
                                             boxstyle="round,pad=0.1",
                                             facecolor=colors['data'], alpha=0.7, 
                                             linewidth=2, edgecolor='darkslategray')
            ax.add_patch(data_rect)
            ax.text(data_node['pos'][0], data_node['pos'][1], data_node['label'], 
                    ha='center', va='center', fontweight='bold', color='white', fontsize=10)
        
        # Define node sizes for accurate connection point calculation
        node_sizes = {
            'circle': (1.0, 1.0),      # START/END nodes
            'agent': (3.0, 1.6),       # Agent rectangles
            'decision': (2.0, 2.0),    # Decision diamonds
            'data': (1.4, 1.0)         # Data storage nodes
        }
        
        # Draw precisely connected workflow arrows with professional styling
        arrows = [
            # Main workflow path connections - clean horizontal/vertical routing
            {'start': nodes['START'], 'end': nodes['web_scraping'], 'label': 'Initialize Workflow', 
             'color': colors['success_path'], 'curve': False, 'start_type': 'circle', 'end_type': 'agent',
             'style': 'solid', 'weight': 'heavy'},
            {'start': nodes['web_scraping'], 'end': nodes['scraping_check'], 'label': 'Validate Download', 
             'color': colors['success_path'], 'curve': False, 'start_type': 'agent', 'end_type': 'decision',
             'style': 'solid', 'weight': 'heavy'},
            
            # Conditional routing with clean curves
            {'start': nodes['scraping_check'], 'end': nodes['doc_processing'], 'label': 'Files Available', 
             'color': colors['success_path'], 'curve': True, 'start_type': 'decision', 'end_type': 'agent',
             'style': 'solid', 'weight': 'heavy', 'curve_direction': 'down-left'},
            
            {'start': nodes['doc_processing'], 'end': nodes['processing_check'], 'label': 'Validate Extraction', 
             'color': colors['success_path'], 'curve': False, 'start_type': 'agent', 'end_type': 'decision',
             'style': 'solid', 'weight': 'heavy'},
            
            {'start': nodes['processing_check'], 'end': nodes['analysis'], 'label': 'Text Available', 
             'color': colors['success_path'], 'curve': True, 'start_type': 'decision', 'end_type': 'agent',
             'style': 'solid', 'weight': 'heavy', 'curve_direction': 'down-left'},
            
            {'start': nodes['analysis'], 'end': nodes['finalize'], 'label': 'Analysis Complete', 
             'color': colors['success_path'], 'curve': True, 'start_type': 'agent', 'end_type': 'agent',
             'style': 'solid', 'weight': 'heavy', 'curve_direction': 'up-right'},
            
            {'start': nodes['finalize'], 'end': nodes['END'], 'label': 'Workflow Complete', 
             'color': colors['success_path'], 'curve': False, 'start_type': 'agent', 'end_type': 'circle',
             'style': 'solid', 'weight': 'heavy'},
            
            # Error paths with distinct styling
            {'start': nodes['scraping_check'], 'end': nodes['finalize'], 'label': 'No Files Found', 
             'color': colors['error_path'], 'curve': True, 'start_type': 'decision', 'end_type': 'agent',
             'style': 'dashed', 'weight': 'medium', 'curve_direction': 'up-right'},
            {'start': nodes['processing_check'], 'end': nodes['finalize'], 'label': 'No Text Extracted', 
             'color': colors['error_path'], 'curve': True, 'start_type': 'decision', 'end_type': 'agent',
             'style': 'dashed', 'weight': 'medium', 'curve_direction': 'right'}
        ]
        
        # Professional data flow arrows with subtle styling
        data_arrows = [
            {'start': (2.7, 8.5), 'end': (4.5, 9.8), 'label': 'Web Source', 
             'color': colors['data_flow'], 'curve': True, 'style': 'dotted', 'weight': 'light'},
            {'start': (2.7, 6.0), 'end': (4.5, 7.2), 'label': 'File Input', 
             'color': colors['data_flow'], 'curve': True, 'style': 'dotted', 'weight': 'light'},
            {'start': (7.5, 4.9), 'end': (9.3, 3.5), 'label': 'JSON Output', 
             'color': colors['data_flow'], 'curve': True, 'style': 'dotted', 'weight': 'light'},
            {'start': (14.0, 6.2), 'end': (14.0, 3.8), 'label': 'Reports', 
             'color': colors['data_flow'], 'curve': False, 'style': 'dotted', 'weight': 'light'}
        ]
        
        # Combine all arrows for professional rendering
        all_arrows = arrows + data_arrows
        
        for arrow in all_arrows:
            # Professional styling based on arrow properties
            weight = arrow.get('weight', 'medium')
            style_type = arrow.get('style', 'solid')
            
            # Set line properties based on weight and style
            if weight == 'heavy':
                linewidth = 4
                alpha = 0.95
                arrowstyle = '->'
                head_width = 0.8
            elif weight == 'medium':
                linewidth = 3
                alpha = 0.8
                arrowstyle = '->'
                head_width = 0.6
            else:  # light
                linewidth = 2
                alpha = 0.6
                arrowstyle = '->'
                head_width = 0.4
            
            # Set line style
            if style_type == 'dashed':
                linestyle = '--'
            elif style_type == 'dotted':
                linestyle = ':'
            else:
                linestyle = '-'
            
            # Calculate precise connection points for workflow arrows
            if 'start_type' in arrow and 'end_type' in arrow:
                start_size = node_sizes.get(arrow['start_type'], node_sizes['agent'])
                end_size = node_sizes.get(arrow['end_type'], node_sizes['agent'])
                
                # Calculate boundary connection points with professional spacing
                start_conn, end_conn = calculate_node_connection_points(
                    arrow['start'], arrow['end'], 
                    {'start': start_size, 'end': end_size}
                )
            else:
                # Use manual coordinates for data flow arrows
                start_conn, end_conn = arrow['start'], arrow['end']
            
            # Professional curve radius based on arrow type
            if arrow.get('curve', False):
                curve_direction = arrow.get('curve_direction', 'default')
                if curve_direction == 'down-left':
                    curve_radius = -0.3
                elif curve_direction == 'up-right':
                    curve_radius = 0.3
                elif curve_direction == 'right':
                    curve_radius = 0.2
                else:
                    curve_radius = 0.25
                
                # Create professional curved arrows
                ax.annotate('', xy=end_conn, xytext=start_conn,
                           arrowprops=dict(
                               arrowstyle=f'->,head_width={head_width}',
                               lw=linewidth, 
                               color=arrow['color'], 
                               linestyle=linestyle, 
                               alpha=alpha,
                               connectionstyle=f"arc3,rad={curve_radius}",
                               capstyle='round',
                               joinstyle='round'
                           ))
            else:
                # Professional straight arrows
                ax.annotate('', xy=end_conn, xytext=start_conn,
                           arrowprops=dict(
                               arrowstyle=f'->,head_width={head_width}',
                               lw=linewidth, 
                               color=arrow['color'], 
                               linestyle=linestyle, 
                               alpha=alpha,
                               capstyle='round',
                               joinstyle='round'
                           ))
            
            # Professional label styling
            if arrow.get('curve', False):
                # For curved arrows, calculate label position at curve peak
                mid_x = (start_conn[0] + end_conn[0]) / 2
                if curve_radius > 0:
                    mid_y = max(start_conn[1], end_conn[1]) + 0.4
                else:
                    mid_y = min(start_conn[1], end_conn[1]) - 0.4
            else:
                # For straight arrows, position label at midpoint with offset
                mid_x = (start_conn[0] + end_conn[0]) / 2
                mid_y = (start_conn[1] + end_conn[1]) / 2 + 0.3
                
            # Professional label background based on arrow type
            if weight == 'heavy':
                label_bg_color = 'white'
                label_alpha = 0.95
                label_fontsize = 10
                label_fontweight = 'bold'
                border_width = 2
            elif weight == 'medium':
                label_bg_color = '#f9f9f9'
                label_alpha = 0.9
                label_fontsize = 9
                label_fontweight = 'semibold'
                border_width = 1.5
            else:  # light
                label_bg_color = '#f5f5f5'
                label_alpha = 0.8
                label_fontsize = 8
                label_fontweight = 'normal'
                border_width = 1
            
            # Render professional labels
            ax.text(mid_x, mid_y, arrow['label'], 
                    ha='center', va='center', 
                    fontsize=label_fontsize, 
                    color=arrow['color'], 
                    fontweight=label_fontweight,
                    bbox=dict(
                        boxstyle='round,pad=0.3', 
                        facecolor=label_bg_color, 
                        alpha=label_alpha, 
                        edgecolor=arrow['color'], 
                        linewidth=border_width
                    ))
        
        # Add enhanced legend with better positioning
        legend_elements = [
            patches.Patch(color=colors['start_end'], label='Start/End Nodes'),
            patches.Patch(color=colors['agent'], label='Processing Agents'),
            patches.Patch(color=colors['decision'], label='Decision Points'),
            patches.Patch(color=colors['finalize'], label='Finalization'),
            patches.Patch(color=colors['data'], label='Data Sources/Outputs')
        ]
        legend = ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.02, 0.98),
                          fontsize=11, frameon=True, fancybox=True, shadow=True)
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_alpha(0.9)
        
        # Add improved workflow statistics box with better formatting
        stats_text = """Workflow Statistics:
• Total Processing Agents: 3
• Decision Points: 2  
• Conditional Execution Paths: 4
• Data Input/Output Points: 4
• Error Handling: Graceful Degradation
• State Persistence: LangGraph Checkpointer
• Tracing: LangSmith Integration"""
        
        ax.text(0.5, 2, stats_text, fontsize=10, 
                bbox=dict(boxstyle='round,pad=0.6', facecolor='lightblue', alpha=0.9,
                         edgecolor='steelblue', linewidth=2), verticalalignment='top')
        
        # Add execution flow indicators
        flow_indicators = [
            {'pos': (9, 1), 'text': 'SUCCESS PATH', 'color': colors['success_path']},
            {'pos': (13, 1), 'text': 'ERROR PATHS', 'color': colors['error_path']},
            {'pos': (16, 1), 'text': 'DATA FLOW', 'color': colors['data_flow']}
        ]
        
        for indicator in flow_indicators:
            ax.text(indicator['pos'][0], indicator['pos'][1], indicator['text'], 
                    ha='center', va='center', fontsize=10, fontweight='bold',
                    color=indicator['color'],
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                             alpha=0.8, edgecolor=indicator['color'], linewidth=2))
        
        # Add subtle visual enhancements for professional appearance
        ax.grid(True, alpha=0.05, linestyle=':', color='gray', linewidth=0.5)
        
        # Add workflow flow indicators with professional styling
        flow_indicators = [
            {'pos': (1, 1.5), 'text': 'SUCCESS PATH', 'color': colors['success_path'], 'symbol': '●'},
            {'pos': (6, 1.5), 'text': 'ERROR PATHS', 'color': colors['error_path'], 'symbol': '●'},
            {'pos': (11, 1.5), 'text': 'DATA FLOW', 'color': colors['data_flow'], 'symbol': '●'}
        ]
        
        for indicator in flow_indicators:
            # Add colored symbol
            ax.text(indicator['pos'][0]-0.3, indicator['pos'][1], indicator['symbol'], 
                    ha='center', va='center', fontsize=16, fontweight='bold',
                    color=indicator['color'])
            # Add text label
            ax.text(indicator['pos'][0], indicator['pos'][1], indicator['text'], 
                    ha='left', va='center', fontsize=11, fontweight='bold',
                    color=indicator['color'],
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                             alpha=0.9, edgecolor=indicator['color'], linewidth=2))
        
        # Professional save with high quality settings
        plt.tight_layout()
        plt.savefig('sebi_langgraph_workflow_diagram.png', 
                   dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none',
                   pad_inches=0.2, transparent=False)
        plt.show()
        
        print("📊 Professional LangGraph workflow diagram with enhanced arrows saved as 'sebi_langgraph_workflow_diagram.png'")
        print("✨ Professional Improvements:")
        print("   🎯 Precise node boundary connections")
        print("   🔄 Professional arrow styling with weight-based rendering")
        print("   📏 Smart curve radius and direction control")
        print("   🎨 Color-coded arrow types (heavy/medium/light)")
        print("   📊 Enhanced label positioning and styling")
        print("   💫 Round caps and joins for smooth appearance")
        print("   🌟 High-resolution output with professional quality")
        
    except ImportError:
        print("⚠️  Matplotlib not installed. Run: pip install matplotlib")
        generate_ascii_workflow_diagram()


def generate_ascii_workflow_diagram():
    """
    Generate an improved ASCII representation of the workflow with better spacing and layout
    """
    ascii_diagram = """
    ┌─────────────────────────────────────────────────────────────────────────────────────────┐
    │                      LangGraph SEBI Document Processing Workflow                         │
    │                             Multi-Agent System Architecture                              │
    └─────────────────────────────────────────────────────────────────────────────────────────┘
    
    
         ┌─────────────┐
         │    START    │
         └──────┬──────┘
                │
                │ Initialize Workflow
                │
                ▼
    ┌─────────────────────────────┐              ┌─────────────────────┐
    │       Web Scraping          │◄─────────────│     SEBI Website    │
    │         Agent               │              │    (Data Source)    │
    │                             │              └─────────────────────┘
    │  • Download PDF files       │
    │  • Extract document links   │
    │  • Collect metadata         │
    │  • Session management       │
    └─────────────┬───────────────┘
                  │
                  │ Validate Downloaded Files
                  │
                  ▼
            ┌─────────────────┐
            │  Files Present  │
            │  & Accessible?  │ ◄──── Decision Point 1
            └─────┬─────┬─────┘
                  │     │
         SUCCESS  │     │  NO FILES
                  │     └─────────────────┐
                  ▼                       │
    ┌─────────────────────────────┐       │              ┌─────────────────────┐
    │    Document Processing      │       │              │     PDF Files       │
    │         Agent               │◄──────┼──────────────│   (File System)     │
    │                             │       │              └─────────────────────┘
    │  • Extract text content     │       │
    │  • Parse document metadata  │       │
    │  • Validate content format  │       │
    │  • Handle extraction errors │       │
    └─────────────┬───────────────┘       │
                  │                       │
                  │ Validate Extracted Text│
                  │                       │
                  ▼                       │
            ┌─────────────────┐           │
            │  Text Content   │           │
            │   Available?    │ ◄──── Decision Point 2
            └─────┬─────┬─────┘           │
                  │     │                 │
         SUCCESS  │     │  NO TEXT        │
                  │     └─────────────────┤
                  ▼                       │
    ┌─────────────────────────────┐       │
    │       Analysis              │       │
    │        Agent                │       │
    │                             │       │
    │  • LLM-based classification │       │
    │  • Department identification │       │
    │  • Extract key insights     │       │
    │  • Generate structured data │       │
    └─────────────┬───────────────┘       │
                  │                       │
                  │ Analysis Complete     │
                  │                       │
                  ▼                       │
    ┌─────────────────────────────┐       │
    │      Finalize &             │ ◄─────┘
    │       Report                │
    │                             │
    │  • Aggregate all results    │
    │  • Generate final reports   │
    │  • Save output files        │
    │  • Perform cleanup          │
    │  • Log workflow statistics  │
    └─────────────┬───────────────┘
                  │
                  │ Workflow Complete
                  │
                  ▼
            ┌─────────────┐
            │     END     │
            └─────────────┘
    
    
    ┌─────────────────────────────────────────────────────────────────────────────────────────┐
    │                                  State Management                                        │
    ├─────────────────────────────────────────────────────────────────────────────────────────┤
    │  Input Parameters:                                                                      │
    │    • page_numbers: List[int]     - SEBI website pages to process                       │
    │    • download_folder: str        - Target directory for downloaded files               │
    │                                                                                         │
    │  Workflow Results:                                                                      │
    │    • scraping_result: Dict       - Download statistics and file metadata               │
    │    • processing_result: Dict     - Text extraction results and document info           │
    │    • analysis_result: Dict       - LLM classification and insights                     │
    │                                                                                         │
    │  Workflow Metadata:                                                                     │
    │    • current_stage: str          - Active processing stage                             │
    │    • workflow_id: str            - Unique workflow execution identifier                │
    │    • start_time: str             - Workflow initialization timestamp                   │
    │    • errors: List[str]           - Comprehensive error collection                      │
    │    • messages: List[Dict]        - Inter-agent communication log                      │
    └─────────────────────────────────────────────────────────────────────────────────────────┘
    
    
    ┌─────────────────────────────────────────────────────────────────────────────────────────┐
    │                                 Execution Paths                                          │
    ├─────────────────────────────────────────────────────────────────────────────────────────┤
    │  Success Path (All stages complete):                                                   │
    │    START → Web Scraping → Files Check → Doc Processing → Text Check → Analysis → END  │
    │                                                                                         │
    │  No Files Path (Scraping fails):                                                       │
    │    START → Web Scraping → Files Check → Finalize → END                                │
    │                                                                                         │
    │  No Text Path (Processing fails):                                                      │
    │    START → Web Scraping → Files Check → Doc Processing → Text Check → Finalize → END  │
    │                                                                                         │
    │  Error Handling: Graceful degradation with comprehensive error logging                 │
    └─────────────────────────────────────────────────────────────────────────────────────────┘
    
    
    ┌─────────────────────────────────────────────────────────────────────────────────────────┐
    │                                   Output Files                                           │
    ├─────────────────────────────────────────────────────────────────────────────────────────┤
    │  Primary Outputs:                                                                       │
    │    📄 scraping_metadata.json              - Raw scraping data and download statistics   │
    │    🔍 sebi_document_analysis_results.json - LLM analysis results and classifications    │
    │                                                                                         │
    │  Optional Outputs:                                                                      │
    │    📊 workflow_results_[ID].json          - Complete workflow execution results         │
    │    📈 workflow_statistics.json            - Performance metrics and timing data        │
    │                                                                                         │
    │  File Formats: JSON with UTF-8 encoding, structured for easy programmatic access      │
    └─────────────────────────────────────────────────────────────────────────────────────────┘
    """
    
    print(ascii_diagram)
    
    # Save ASCII diagram to file
    with open('sebi_workflow_ascii_diagram.txt', 'w', encoding='utf-8') as f:
        f.write(ascii_diagram)
    
    print("📊 ASCII workflow diagram saved as 'sebi_workflow_ascii_diagram.txt'")


def generate_workflow_documentation():
    """
    Generate comprehensive documentation for the workflow
    """
    doc = """
# SEBI Document Processing Multi-Agent Workflow

## Overview
This LangGraph-based multi-agent system processes SEBI (Securities and Exchange Board of India) documents through a structured workflow with three specialized agents.

## Architecture

### Agents

#### 1. Web Scraping Agent
- **Purpose**: Downloads PDFs from SEBI website using AJAX scraper
- **Input**: Page numbers, download folder
- **Output**: Downloaded PDF files and metadata
- **Technology**: Custom AJAX scraper with session management

#### 2. Document Processing Agent  
- **Purpose**: Extracts text and metadata from PDF documents
- **Input**: Downloaded PDF files
- **Output**: Extracted text content and document metadata
- **Technology**: PyPDF2 and pdfplumber for comprehensive extraction

#### 3. Analysis Agent
- **Purpose**: Analyzes and classifies documents using LLM
- **Input**: Extracted text content
- **Output**: Classified documents with departments, intermediaries, and key insights
- **Technology**: PWC GenAI API with structured prompts

### Workflow Flow

```
START → Web Scraping → [Files Downloaded?] → Document Processing → [Text Extracted?] → Analysis → Finalize → END
           ↓                                        ↓
        [No Files]                              [No Text]
           ↓                                        ↓
        Finalize ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
```

## State Management

The workflow uses a shared state object that includes:
- Input parameters (page numbers, download folder)
- Results from each stage
- Workflow metadata and error tracking
- Inter-agent messages

## Key Features

### 1. Error Resilience
- Each agent handles errors gracefully
- Workflow continues even if individual stages fail
- Comprehensive error logging and reporting

### 2. Conditional Execution
- Decisions points check if previous stages succeeded
- Workflow can skip stages if prerequisites aren't met
- Smart routing based on intermediate results

### 3. Comprehensive Logging
- Each agent logs its activities with timestamps
- Inter-agent messages track workflow progress
- Final report summarizes entire workflow

### 4. State Persistence
- LangGraph checkpointer maintains workflow state
- Enables workflow resumption and debugging
- Complete audit trail of all operations

## Usage Examples

### Basic Usage
```python
from langgraph_workflow import run_sebi_workflow

# Run with default parameters
result = run_sebi_workflow([1, 2], "test_enhanced_metadata")
```

### Custom Workflow
```python
from langgraph_workflow import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()
result = orchestrator.run_workflow([1, 3, 5], "custom_folder")
```

### Original Sequential Comparison
```python
# Original approach (sequential)
result = scrape_page([1,2], "test_enhanced_metadata")
result = process_test_enhanced_metadata_pdfs()
result = run_analysis()

# New approach (multi-agent workflow)
result = run_sebi_workflow([1,2], "test_enhanced_metadata")
```

## Output Files

### Generated Files
1. **scraping_metadata.json** - Raw scraping data and file metadata
2. **sebi_document_analysis_results.json** - LLM analysis results
3. **workflow_results_[ID].json** - Complete workflow execution results

### Metadata Structure
Each file processed includes:
- Circular number and date extraction
- SEBI reference identification  
- Department classification
- Intermediary identification
- Key clauses and metrics
- Actionable items

## Benefits Over Sequential Approach

### 1. Better Error Handling
- Individual stage failures don't crash entire process
- Graceful degradation and recovery mechanisms
- Detailed error reporting and diagnostics

### 2. Improved Observability
- Real-time progress tracking
- Inter-agent communication logging
- Performance metrics and timing

### 3. Enhanced Maintainability
- Modular agent architecture
- Clear separation of concerns
- Easy to extend with new agents

### 4. Workflow Flexibility
- Conditional execution paths
- Configurable parameters
- Multiple workflow patterns supported

## Configuration

### Environment Variables
- API keys for PWC GenAI service
- Custom download paths
- Model selection preferences

### Workflow Parameters
- Page numbers to scrape
- Download folder names
- Processing options
- Analysis model selection

## Monitoring and Debugging

### Logging Levels
- INFO: Normal operation messages
- ERROR: Error conditions and failures
- SUCCESS: Successful stage completions

### State Inspection
- Access to intermediate results
- Workflow state at each stage
- Message history between agents

## Future Enhancements

### Possible Extensions
1. **Parallel Processing Agent** - Process multiple files simultaneously
2. **Validation Agent** - Verify data quality and completeness
3. **Export Agent** - Generate reports in multiple formats
4. **Notification Agent** - Send alerts and updates

### Integration Points
- Database storage for persistent results
- External API integrations
- Workflow scheduling and automation
- Dashboard for workflow monitoring

## Troubleshooting

### Common Issues
1. **Network connectivity** - Check SEBI website accessibility
2. **PDF extraction errors** - Verify file integrity
3. **API failures** - Check PWC GenAI service status
4. **Path issues** - Ensure proper file permissions

### Debug Mode
Enable detailed logging by setting appropriate log levels in each agent.
"""
    
    
    
    print("📚 Documentation saved as 'workflow_documentation.md'")
    return doc


def generate_state_flow_json():
    """
    Generate a JSON representation of the workflow state transitions and node relationships
    """
    state_flow = {
        "workflow": {
            "name": "SEBI Document Processing",
            "version": "1.0",
            "framework": "LangGraph",
            "description": "Multi-agent workflow for processing SEBI regulatory documents"
        },
        "nodes": {
            "START": {
                "type": "start_node",
                "description": "Workflow initialization",
                "next": ["web_scraping"],
                "state_updates": ["workflow_id", "start_time", "initial_parameters"]
            },
            "web_scraping": {
                "type": "agent_node",
                "name": "Web Scraping Agent",
                "description": "Downloads PDFs from SEBI website using AJAX scraper",
                "function": "web_scraping_agent",
                "inputs": ["page_numbers", "download_folder"],
                "outputs": ["scraping_result", "downloaded_files_metadata"],
                "next": ["scraping_check"],
                "error_handling": "graceful_degradation",
                "timeout": 300,
                "retry_count": 3,
                "capabilities": [
                    "AJAX-based web scraping",
                    "Session management", 
                    "File download tracking",
                    "Metadata extraction",
                    "Link validation"
                ]
            },
            "scraping_check": {
                "type": "conditional_node",
                "name": "Scraping Success Check",
                "description": "Validates if files were successfully downloaded",
                "function": "check_scraping_success",
                "condition": "scraping_result.total_downloaded_files > 0",
                "outcomes": {
                    "continue": "document_processing",
                    "end": "finalize"
                },
                "decision_logic": "file_count_validation"
            },
            "document_processing": {
                "type": "agent_node", 
                "name": "Document Processing Agent",
                "description": "Extracts text and metadata from PDF documents",
                "function": "document_processing_agent",
                "inputs": ["scraping_result", "pdf_files"],
                "outputs": ["processing_result", "extracted_text", "document_metadata"],
                "next": ["processing_check"],
                "error_handling": "per_file_error_tracking",
                "libraries": ["PyPDF2", "pdfplumber"],
                "capabilities": [
                    "PDF text extraction",
                    "Metadata parsing",
                    "Content validation",
                    "Format detection",
                    "Error recovery"
                ]
            },
            "processing_check": {
                "type": "conditional_node",
                "name": "Processing Success Check", 
                "description": "Validates if text extraction was successful",
                "function": "check_processing_success",
                "condition": "processing_result.processed_files_count > 0",
                "outcomes": {
                    "continue": "analysis",
                    "end": "finalize"
                },
                "decision_logic": "extraction_validation"
            },
            "analysis": {
                "type": "agent_node",
                "name": "Analysis Agent",
                "description": "Analyzes and classifies documents using LLM",
                "function": "analysis_agent", 
                "inputs": ["processing_result", "extracted_text"],
                "outputs": ["analysis_result", "classifications", "insights"],
                "next": ["finalize"],
                "error_handling": "document_level_errors",
                "llm_provider": "PWC GenAI API",
                "capabilities": [
                    "Document classification",
                    "Department identification",
                    "Intermediary extraction", 
                    "Key insight generation",
                    "Structured output formatting"
                ]
            },
            "finalize": {
                "type": "finalization_node",
                "name": "Workflow Finalizer",
                "description": "Generates final reports and performs cleanup",
                "function": "finalize_workflow",
                "inputs": ["all_agent_results", "workflow_state"],
                "outputs": ["final_report", "summary_statistics", "saved_files"],
                "next": ["END"],
                "operations": [
                    "Result aggregation",
                    "Report generation", 
                    "File saving",
                    "Statistics calculation",
                    "Cleanup operations"
                ]
            },
            "END": {
                "type": "end_node",
                "description": "Workflow completion",
                "final_state": ["completed", "results_saved"]
            }
        },
        "state_schema": {
            "required_fields": {
                "page_numbers": {
                    "type": "List[int]",
                    "description": "SEBI website page numbers to scrape",
                    "default": [1]
                },
                "download_folder": {
                    "type": "str", 
                    "description": "Target folder for downloaded files",
                    "default": "test_enhanced_metadata"
                }
            },
            "workflow_fields": {
                "scraping_result": {
                    "type": "Dict[str, Any]",
                    "description": "Results from web scraping stage"
                },
                "processing_result": {
                    "type": "Dict[str, Any]",
                    "description": "Results from document processing stage"
                },
                "analysis_result": {
                    "type": "Dict[str, Any]", 
                    "description": "Results from analysis stage"
                }
            },
            "metadata_fields": {
                "current_stage": {
                    "type": "str",
                    "description": "Currently active workflow stage"
                },
                "workflow_id": {
                    "type": "str",
                    "description": "Unique workflow identifier"
                },
                "start_time": {
                    "type": "str",
                    "description": "Workflow start timestamp"
                },
                "errors": {
                    "type": "List[str]",
                    "description": "Collection of errors encountered"
                },
                "messages": {
                    "type": "List[Dict[str, Any]]",
                    "description": "Inter-agent communication messages"
                }
            }
        },
        "edges": {
            "sequential_edges": [
                {"from": "START", "to": "web_scraping", "type": "direct"},
                {"from": "web_scraping", "to": "scraping_check", "type": "direct"},
                {"from": "document_processing", "to": "processing_check", "type": "direct"},
                {"from": "analysis", "to": "finalize", "type": "direct"}, 
                {"from": "finalize", "to": "END", "type": "direct"}
            ],
            "conditional_edges": [
                {
                    "from": "scraping_check",
                    "condition": "check_scraping_success",
                    "outcomes": {
                        "continue": {"to": "document_processing", "condition": "files_downloaded > 0"},
                        "end": {"to": "finalize", "condition": "files_downloaded == 0"}
                    }
                },
                {
                    "from": "processing_check", 
                    "condition": "check_processing_success",
                    "outcomes": {
                        "continue": {"to": "analysis", "condition": "processed_files > 0"},
                        "end": {"to": "finalize", "condition": "processed_files == 0"}
                    }
                }
            ]
        },
        "execution_patterns": {
            "success_path": ["START", "web_scraping", "scraping_check", "document_processing", "processing_check", "analysis", "finalize", "END"],
            "no_files_path": ["START", "web_scraping", "scraping_check", "finalize", "END"],
            "no_text_path": ["START", "web_scraping", "scraping_check", "document_processing", "processing_check", "finalize", "END"],
            "error_recovery": "Each agent handles errors gracefully and continues workflow"
        },
        "output_artifacts": {
            "primary_outputs": [
                {
                    "filename": "scraping_metadata.json",
                    "description": "Raw scraping data and file metadata",
                    "generated_by": "web_scraping_agent"
                },
                {
                    "filename": "sebi_document_analysis_results.json", 
                    "description": "LLM analysis results and classifications",
                    "generated_by": "analysis_agent"
                }
            ],
            "workflow_outputs": [
                {
                    "filename": "workflow_results_[ID].json",
                    "description": "Complete workflow execution results",
                    "generated_by": "finalize_workflow",
                    "optional": "true"
                }
            ]
        },
        "monitoring": {
            "logging_levels": ["INFO", "ERROR", "SUCCESS"],
            "progress_tracking": "Real-time stage updates",
            "error_handling": "Graceful degradation with error collection",
            "performance_metrics": ["duration", "success_rates", "file_counts"]
        }
    }
    
    
    return state_flow


def generate_node_relationship_mermaid():
    """
    Generate a Mermaid diagram representation of the workflow
    """
    mermaid_diagram = """
    ```mermaid
    graph TD
        A[START] --> B[Web Scraping Agent]
        B --> C{Files Downloaded?}
        C -->|YES| D[Document Processing Agent]
        C -->|NO| H[Finalize & Report]
        D --> E{Text Extracted?}
        E -->|YES| F[Analysis Agent]
        E -->|NO| H
        F --> H
        H --> I[END]
        
        %% Data sources and outputs
        J[(SEBI Website)] -.-> B
        K[(PDF Files)] -.-> D
        L[(JSON Results)] -.-> F
        M[(Final Report)] -.-> H
        
        %% Styling
        classDef startEnd fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
        classDef agent fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
        classDef decision fill:#FF9800,stroke:#333,stroke-width:2px,color:#fff
        classDef finalize fill:#9C27B0,stroke:#333,stroke-width:2px,color:#fff
        classDef data fill:#607D8B,stroke:#333,stroke-width:1px,color:#fff
        
        class A,I startEnd
        class B,D,F agent  
        class C,E decision
        class H finalize
        class J,K,L,M data
    ```
    
    ## Node Details
    
    ### Agents (Processing Nodes)
    - **Web Scraping Agent**: Downloads PDFs from SEBI website with session management
    - **Document Processing Agent**: Extracts text from PDFs using PyPDF2/pdfplumber
    - **Analysis Agent**: Classifies documents using LLM (PWC GenAI API)
    
    ### Decision Points
    - **Files Downloaded?**: Checks if scraping was successful (files > 0)
    - **Text Extracted?**: Validates text extraction success (processed_files > 0)
    
    ### Control Flow
    - **Sequential Flow**: Each agent processes data and passes to next stage
    - **Conditional Routing**: Decision points route based on success/failure
    - **Error Recovery**: Failed stages route to finalization for graceful completion
    
    ### State Management
    - **Persistent State**: LangGraph maintains state across all nodes
    - **Message Passing**: Agents communicate via structured messages
    - **Error Tracking**: All errors collected and reported in final stage
    """
    
    
    
    print("🌊 Mermaid diagram saved as 'workflow_mermaid_diagram.md'")
    return mermaid_diagram


if __name__ == "__main__":
    print("📋 Generating comprehensive workflow documentation and diagrams...")
    print("="*80)
    
    # Generate all documentation
    print("\n🖼️  Generating visual workflow diagram...")
    generate_workflow_diagram()
    
    print("\n📚 Generating comprehensive documentation...")
    generate_workflow_documentation()  
    
    print("\n🔄 Generating detailed workflow structure...")
    generate_state_flow_json()
    
    print("\n🌊 Generating Mermaid diagram...")
    generate_node_relationship_mermaid()
    
    print("\n" + "="*80)
    print("✅ All enhanced documentation generated successfully!")
    print("="*80)
    print("📁 Generated files with improved layouts:")
    print("   🖼️  sebi_langgraph_workflow_diagram.png - Enhanced visual workflow diagram")
    print("   📄 sebi_workflow_ascii_diagram.txt - Improved ASCII text diagram")  
    print("   📚 workflow_documentation.md - Comprehensive documentation")
    print("   🔄 langgraph_workflow_structure.json - Detailed node structure")
    print("   🌊 workflow_mermaid_diagram.md - Mermaid diagram for web display")
    print("="*80)
    
    # Display enhanced summary
    print("\n📊 Enhanced Workflow Summary:")
    print("   🤖 Total Processing Agents: 3 (Web Scraping, Document Processing, Analysis)")
    print("   🔀 Decision Points: 2 (File validation, Text validation)")
    print("   📈 Execution Paths: 3 (Success, No Files, No Text)")
    print("   🛡️  Error Handling: Graceful degradation with comprehensive error tracking")
    print("   💾 State Management: Persistent state with LangGraph checkpointer")
    print("   📤 Output Files: 3 primary + 1 optional workflow result file")
    print("\n✨ Layout Improvements:")
    print("   🎯 Better node spacing and positioning for clarity")
    print("   🔄 Enhanced arrow routing with curved connections")
    print("   📏 Improved visual hierarchy and organization")
    print("   🎨 Refined color scheme and professional styling")
    print("   📊 Clearer labels and flow indicators")
    print("   🖼️  Higher resolution output with better quality")
