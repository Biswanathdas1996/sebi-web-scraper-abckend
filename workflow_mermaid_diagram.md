
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
    