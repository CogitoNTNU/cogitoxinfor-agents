#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF Test Generator

This module combines functionality from various notebooks to create a system
that can generate tests based on retrieved PDFs.
"""

# Import necessary libraries
import os
import re
import uuid
import base64
import io
from typing import Annotated, List, Optional, Literal, Dict, Any
from dotenv import load_dotenv
import fitz  # PyMuPDF
from PIL import Image as PILImage
from IPython.display import Image as IPImage, display
import operator
from pydantic import BaseModel, Field

# LangChain imports
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import AstraDB
from langchain.chains import TransformChain
from langchain_core.runnables import chain
from langchain_core.output_parsers import JsonOutputParser

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
load_dotenv()

# Get API keys from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASTRA_DB_API_KEY = os.getenv('ASTRA_DB_API_KEY')
ASTRA_DB_ENDPOINT = os.getenv('ASTRA_DB_ENDPOINT')
ASTRA_DB_KEYSPACE = os.getenv('ASTRA_DB_KEYSPACE')

# ============================================================================
# Utility Functions
# ============================================================================

def load_model(model_name: str = "gpt-4o", tools=None):
    """Load the model dynamically based on the parameter."""
    model = ChatOpenAI(
        model=model_name,
        temperature=0,
    )
    # Bind tools if provided
    if tools:
        model = model.bind_tools(tools)
    
    return model

def get_vectorstore(collection_name: str) -> AstraDB:
    """Get the vector store for document retrieval."""
    embeddings = OpenAIEmbeddings()
    return AstraDB(
        embedding=embeddings,
        token=ASTRA_DB_API_KEY,
        api_endpoint=ASTRA_DB_ENDPOINT,
        collection_name=collection_name,
    )

def pdf_page_to_base64(pdf_path: str, page_number: int) -> str:
    """Convert a PDF page to a base64-encoded image."""
    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(page_number - 1)  # input is one-indexed
    pix = page.get_pixmap()
    img = PILImage.frombytes("RGB", [pix.width, pix.height], pix.samples)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def get_pdf_text_content(pdf_path: str) -> List[Document]:
    """Extract text content from a PDF file."""
    pdf_document = fitz.open(pdf_path)
    documents = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        page_content = page.get_text()
        document = CustomDocument(
            page_content=page_content,
            metadata={
                "source": pdf_path, 
                "page_number": page_num + 1,
                "file_name": os.path.basename(pdf_path),
            }
        )
        documents.append(document)
    return documents

def preprocess_content(content):
    """Remove specific phrases from the content."""
    # This can be customized based on the specific PDFs being processed
    return re.sub(r'Enable Internal Sales Orders \(Internal Sales Orders\) \d+ \(\d+\)', '', content)

def split_by_headers(documents, header_pattern, specific_headers):
    """Split documents by headers."""
    split_docs = []
    last_seen_header = None
    for doc in documents:
        # Preprocess the content to remove the specific phrase
        content = preprocess_content(doc.page_content)
        chunks = re.split(f'({header_pattern})', content)
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        for chunk in chunks:
            if chunk in specific_headers:
                last_seen_header = chunk
            else:
                split_docs.append(
                    Document(
                        page_content=chunk,
                        metadata={'header': last_seen_header}
                    )
                )
    return split_docs

def metadata_retriever_tool(query: str, rag_collection: str = "not_metadata") -> str:
    """Retrieve documents based on a user query and return context."""
    vectorstore = get_vectorstore(rag_collection)
    model = load_model()
    retriever = SelfQueryRetriever.from_llm(
        model, 
        vectorstore, 
        document_content_description, 
        metadata_field_info, 
        verbose=True,
        search_kwargs={"k": 10},
    )
    retrieved_documents = retriever.invoke(query)
    context = "<br />".join([doc.page_content for doc in retrieved_documents])
    return context

# ============================================================================
# Document and State Classes
# ============================================================================

class CustomDocument(Document):
    """Custom document class with image content field."""
    id: Optional[str] = None
    metadata: Optional[dict] = None
    page_content: str
    image_content: Optional[str] = None
    type: Literal['Document'] = 'Document'

class PDF(BaseModel):
    """PDF class containing a list of custom documents."""
    id: uuid.UUID
    documents: Annotated[List[CustomDocument], operator.add] = Field(default_factory=list)

class TestCase(BaseModel):
    """Test case generated from PDF content."""
    id: str
    title: str
    description: str
    steps: List[str]
    expected_results: List[str]
    requirements: List[str]

class InputState(BaseModel):
    """Input state for the graph."""
    requirements: List[str]
    data_path: str

class AgentState(BaseModel):
    """Main state for the graph."""
    next_agent: str = ""
    llm_model_name: str = "gpt-4o-mini"
    pdfs: Annotated[List[PDF], operator.add] = Field(default_factory=list)
    error_message: Annotated[str, operator.add] = ""
    data_path: str = "../data"  # Updated to point to thomas/data
    files: List[str] = Field(default_factory=list)
    chosen_files: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    test_cases: List[TestCase] = Field(default_factory=list)  # Added to store test cases

class DocumentState(BaseModel):
    """State for each agent that retrieves image content."""
    document: Annotated[List[CustomDocument], operator.add]
    data_path: str
    error_message: Annotated[str, operator.add] = ""
    llm_model_name: str = "gpt-4o-mini"

class RetrieverOutput(BaseModel):
    """Output from the retriever agent."""
    pdf_files: List[str]

class ImageInformation(BaseModel):
    """Information about an image."""
    image_description: str = Field(description="a short description of the image")
    people_count: int = Field(description="number of humans on the picture")
    main_objects: list[str] = Field(description="list of the main objects on the picture")
    humans: int = Field(description="number of humans on the picture")

# ============================================================================
# Graph Nodes
# ============================================================================

# Node names
GET_PDF_FILES = "get_pdf_files"
RETRIEVER_AGENT = "retriever_agent"
GET_TEXT_CONTENT = "get_text_content"
GET_IMAGE_CONTENT = "get_image_content"
GENERATE_TESTS = "generate_tests"

# Global variables
files = []
document_content_description = "The pages"
metadata_field_info = [
    AttributeInfo(
        name='header',
        description="The 'header' of the page. The 'header' is one of ['Overview', 'Tasks', 'Setup', 'Additional information']",
        type="string",
    ),
]

def get_pdf_files(state: AgentState):
    """Get PDF files from the data directory."""
    global files
    files = []
    try:
        data_path = state.data_path
        # Get the files in the data directory
        for file in os.listdir(data_path):
            if file.endswith(".pdf"):
                files.append(file)
    except Exception as e:
        state.error_message = f"An error occurred while retrieving the files: {e}"
        return state
    
    state.files = files
    return state

def create_retrieve_agent(chat_prompt: ChatPromptTemplate, parser: BaseModel = None):
    """Create an agent for retrieving PDFs based on requirements."""
    def agent(state):
        llm = load_model(model_name=state.llm_model_name)

        # Invoking the prompt template with the values from the state
        prompt = chat_prompt.invoke(input={
            "files": state.files,
            "requirements": state.requirements
        })

        try:
            # Use structured output if parser is provided
            if parser:
                llm_with_structured_output = llm.with_structured_output(schema=parser)
                response = llm_with_structured_output.invoke(prompt)
                print(f"Response: {response}")
                chosen_files = response.pdf_files
            else:
                # Fallback to direct selection
                chosen_files = []
            
            # Ensure at least one file is chosen
            if len(chosen_files) == 0 and len(state.files) > 0:
                print("No files were chosen by the agent. Using all available PDF files.")
                chosen_files = state.files
            
            state.chosen_files = chosen_files
            
            if len(chosen_files) == 0:
                state.error_message = "No PDF files found in the data directory."
                state.next_agent = END
            else:
                state.next_agent = GET_TEXT_CONTENT
            
        except Exception as e:
            # If there's an error, use all available files
            print(f"An error occurred: {e}. Using all available PDF files.")
            if len(state.files) > 0:
                state.chosen_files = state.files
                state.next_agent = GET_TEXT_CONTENT
            else:
                state.error_message = f"An error occurred and no PDF files are available: {e}"
                state.next_agent = END
            
        return state

    return agent

def get_text_content(state: AgentState) -> AgentState:
    """Extract text content from chosen PDFs."""
    pdf_path = state.data_path
    files = state.chosen_files
    for file in files:
        pdf_content = get_pdf_text_content(f"{pdf_path}/{file}")
        pdf = PDF(id=uuid.uuid4(), documents=pdf_content)
        state.pdfs.append(pdf)
    print("Saved the following text from pdfs: ", state.pdfs)
    return state

def get_image_content_agent():
    """Create an agent for extracting image content from PDF pages."""
    async def agent(state: DocumentState):
        llm = load_model(model_name=state.llm_model_name)
        pdf_path = state.data_path
        document = state.document[0]
        try:
            page_num = document.metadata["page_number"]
            file = document.metadata["file_name"]
            base64_image = pdf_page_to_base64(f"{pdf_path}/{file}", page_num)
            print(f"Inferring the image content of page {page_num} in {file}")
            # Define the query
            query = f"Analyze the content of the image in {page_num}"

            # Create the message with text and image
            message = HumanMessage(
                content=[
                    {"type": "text", "text": query},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            )

            # Query the model
            response = await llm.ainvoke([message])
            document.image_content = response.content

            return {"document": [document]}
        except Exception as e:
            return {"error_message": f"An error occurred while generating variables: {e}"}

    return agent

def continue_to_analyze_documents(state: AgentState):
    """Create a list of Send objects for parallel document processing."""
    return [
        Send(
            GET_IMAGE_CONTENT, 
            DocumentState(
                document=[document],
                data_path=state.data_path,
                error_message=state.error_message,
                llm_model_name=state.llm_model_name,
            )
        ) 
        for pdf in state.pdfs  # Iterate over each PDF
        for document in pdf.documents  # Iterate over each document
    ]

def generate_tests_agent():
    """Create an agent for generating tests from PDF content."""
    def agent(state: AgentState):
        llm = load_model(model_name="gpt-4o")  # Use a more capable model for test generation
        
        # Collect all PDF content
        all_text_content = []
        file_names = []
        
        for pdf in state.pdfs:
            for doc in pdf.documents:
                if doc.page_content.strip():  # Only include non-empty content
                    all_text_content.append(doc.page_content)
                    file_names.append(doc.metadata["file_name"])
        
        # Join all text content
        combined_content = "\n\n".join(all_text_content)
        
        # Get a unique file name
        file_name = file_names[0] if file_names else "Unknown"
        
        # Create a prompt specifically for extracting test steps from the PDF content
        extraction_prompt = f"""
        I have a PDF file named '{file_name}' with the following content:

        {combined_content[:10000]}  # Limit content to avoid token limits
        
        Based on this PDF content and these requirements:
        {state.requirements}
        
        Please create a detailed test case that specifically tests the functionality described in the PDF.
        Go step by step through the process and describe the expected results for each step in detail.
        
        Your response should be in this JSON format:
        {{
            "id": "A unique identifier for the test case",
            "title": "A descriptive title based on the PDF content",
            "description": "A detailed description that references specific content from the PDF",
            "steps": [
                "Step 1: A specific action based on the PDF content",
                "Step 2: Another specific action based on the PDF content",
                "Step 3: Another specific action based on the PDF content"
            ],
            "expected_results": [
                "Expected result for step 1 based on the PDF content",
                "Expected result for step 2 based on the PDF content",
                "Expected result for step 3 based on the PDF content"
            ]
        }}
        
        IMPORTANT: Your test steps and expected results MUST be specific to the actual content of the PDF. 
        Do not use generic steps like "Open the application" unless specifically mentioned in the PDF.
        Include specific field names, actions, and processes mentioned in the PDF.
        REMEBER TO INCLUDE INPUT VALUES, ACTIONS, AND EXPECTED RESULTS BASED ON THE PDF CONTENT.
        """
        
        try:
            # Get the LLM's response
            response = llm.invoke(extraction_prompt)
            content = response.content
            
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON pattern in the response
            json_match = re.search(r'({[\s\S]*})', content)
            if json_match:
                json_str = json_match.group(1)
                try:
                    test_data = json.loads(json_str)
                    
                    # Create a test case from the extracted data
                    test_case = TestCase(
                        id=test_data.get("id", f"PDF-{uuid.uuid4().hex[:8].upper()}"),
                        title=test_data.get("title", f"Test Case for {file_name}"),
                        description=test_data.get("description", f"Test case for {file_name}"),
                        steps=test_data.get("steps", []),
                        expected_results=test_data.get("expected_results", []),
                        requirements=state.requirements
                    )
                    
                    # Add the test case to the state
                    state.test_cases = [test_case]
                    return state
                except json.JSONDecodeError:
                    # If JSON parsing fails, fall back to text extraction
                    pass
            
            # If JSON extraction failed, try to extract information from the text
            # Extract steps (look for numbered lists or lines starting with "Step")
            steps = []
            expected_results = []
            
            # Look for steps in the content
            step_matches = re.findall(r'(?:Step \d+:|^\d+\.)\s*(.*?)(?=(?:Step \d+:|^\d+\.)|$)', content, re.MULTILINE)
            if step_matches:
                steps = [step.strip() for step in step_matches if step.strip()]
            
            # Look for expected results
            result_matches = re.findall(r'(?:Expected result|Expected outcome|Result).*?:\s*(.*?)(?=(?:Expected|Result|\d+\.)|$)', content, re.MULTILINE | re.IGNORECASE)
            if result_matches:
                expected_results = [result.strip() for result in result_matches if result.strip()]
            
            # If we couldn't extract steps or results, create some based on the content
            if not steps:
                # Extract key sentences that might be steps
                sentences = re.split(r'(?<=[.!?])\s+', content)
                action_sentences = [s for s in sentences if re.search(r'\b(?:click|enter|select|verify|check|open|navigate|input|submit|create|add|delete|update)\b', s, re.IGNORECASE)]
                steps = action_sentences[:5] if action_sentences else ["No specific steps could be extracted from the PDF content"]
            
            if not expected_results:
                # Create expected results based on steps
                expected_results = [f"The action '{step}' completes successfully" for step in steps]
            
            # Ensure we have the same number of expected results as steps
            while len(expected_results) < len(steps):
                expected_results.append(f"The action completes successfully")
            
            # Trim expected_results to match steps length
            expected_results = expected_results[:len(steps)]
            
            # Extract a title from the content
            title_match = re.search(r'Title:?\s*(.*?)(?=\n|$)', content)
            title = title_match.group(1) if title_match else f"Test Case for {file_name}"
            
            # Extract a description from the content
            desc_match = re.search(r'Description:?\s*(.*?)(?=\n|$)', content)
            description = desc_match.group(1) if desc_match else f"Test case based on content from {file_name}"
            
            # Create the test case
            test_case = TestCase(
                id=f"PDF-{uuid.uuid4().hex[:8].upper()}",
                title=title,
                description=description,
                steps=steps,
                expected_results=expected_results,
                requirements=state.requirements
            )
            
            # Add the test case to the state
            state.test_cases = [test_case]
            
        except Exception as e:
            state.error_message = f"An error occurred while generating test cases: {e}"
            print(f"Error in test generation: {e}")
        
        return state
    
    return agent

# ============================================================================
# Graph Setup
# ============================================================================

def setup_graph():
    """Set up the LangGraph workflow."""
    # Create the retriever prompt
    system_instructions = """
    You are an expert at retrieving the correct PDFs based on some requirements from the user.
    Analyze the requirements and retrieve the correct PDFs and find the correct PDF.
    There are following PDFs you can retrieve content from:
    examples:
        user: Here is my requirements: ['requirement1', 'requirement2']
        ai-agent: [file.pdf, file2.pdf]

        user: Here is my requirements: ['requirement1', 'requirement2', 'requirement3']
        ai-agent: [file.pdf]
    """

    query_data = """
    Here are the pdf files you can retrieve:
    {files}

    Which files do you want to retrieve content from given these requirements: 
    {requirements}
    """

    retrieve_prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("human", query_data),
    ])

    # Create the retriever agent
    retriever_agent = create_retrieve_agent(
        chat_prompt=retrieve_prompt,
        parser=RetrieverOutput,
    )

    # Create the image content agent
    image_content_agent = get_image_content_agent()

    # Create the test generation agent
    test_generator = generate_tests_agent()

    # Create the graph
    builder = StateGraph(state_schema=AgentState, input=InputState)

    # Add nodes to the graph
    builder.add_node(GET_PDF_FILES, get_pdf_files)
    builder.add_node(RETRIEVER_AGENT, retriever_agent)
    builder.add_node(GET_TEXT_CONTENT, get_text_content)
    builder.add_node(GET_IMAGE_CONTENT, image_content_agent)
    builder.add_node(GENERATE_TESTS, test_generator)

    # Add edges to the graph
    builder.add_edge(START, GET_PDF_FILES)
    builder.add_edge(GET_PDF_FILES, RETRIEVER_AGENT)
    builder.add_edge(RETRIEVER_AGENT, GET_TEXT_CONTENT)
    builder.add_conditional_edges(
        GET_TEXT_CONTENT, 
        continue_to_analyze_documents, 
        [GET_IMAGE_CONTENT]
    )
    builder.add_edge(GET_IMAGE_CONTENT, GENERATE_TESTS)
    builder.add_edge(GENERATE_TESTS, END)

    # Set up memory checkpointer
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    return graph

# ============================================================================
# Main Function for Test Generation
# ============================================================================

async def generate_tests_from_pdfs(requirements: List[str], data_path: str = "../data"):
    """
    Generate tests based on retrieved PDFs.
    
    Args:
        requirements: List of requirements for the tests
        data_path: Path to the directory containing PDF files
        
    Returns:
        List of generated test cases
    """
    # Set up the graph
    graph = setup_graph()
    
    # Create a unique thread ID for this run
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
        }
    }
    
    # Create the input state
    state = InputState(
        requirements=requirements,
        data_path=data_path,
    )
    
    # Run the graph
    print("Starting PDF test generation process...")
    output_state = await graph.ainvoke(state, config)
    
    # Check for errors
    if 'error_message' in output_state and output_state['error_message']:
        print(f"Error: {output_state['error_message']}")
        return []
    
    # Return the generated test cases
    if 'test_cases' in output_state and output_state['test_cases']:
        return output_state['test_cases']
    else:
        # Create a default test case if none were generated
        print("No test cases were generated. Creating a default test case.")
        return [
            TestCase(
                id="DEFAULT-001",
                title="Default Test Case",
                description="This is a default test case created when no test cases could be generated from the PDF content.",
                steps=["Step 1: Open the application", "Step 2: Navigate to the relevant section", "Step 3: Perform the required action"],
                expected_results=["Result 1: Application opens successfully", "Result 2: Navigation completes successfully", "Result 3: Action is performed successfully"],
                requirements=requirements
            )
        ]

# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        # Example requirements
        requirements = [
            "Test the process of creating an internal sales order",
            "Verify that all required fields are validated",
            "Check that the order can be submitted successfully"
        ]

        # Generate tests
        test_cases = await generate_tests_from_pdfs(requirements)

        # Prepare the output string
        output_lines = [f"Generated {len(test_cases)} test cases:"]
        for test in test_cases:
            output_lines.append(f"\nTest ID: {test.id}")
            output_lines.append(f"Title: {test.title}")
            output_lines.append(f"Description: {test.description}")
            output_lines.append("Steps:")
            for i, step in enumerate(test.steps, 1):
                output_lines.append(f"  {i}. {step}")
            output_lines.append("Expected Results:")
            for i, result in enumerate(test.expected_results, 1):
                output_lines.append(f"  {i}. {result}")
            output_lines.append("Requirements:")
            for req in test.requirements:
                output_lines.append(f"  - {req}")

        output = "\n".join(output_lines)

        # Print the generated test cases
        print(output)

        # Write the output to test.txt
        with open("test.txt", "w") as f:
            f.write(output)

    # Run the example
    asyncio.run(main())
