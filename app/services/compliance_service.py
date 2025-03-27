"""
Service for verifying prompt compliance with policies using RAG approach.
"""
import logging
import os
import re
import json
import uuid
import shutil
from typing import List, Dict, Any, Optional, Tuple

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, DirectoryLoader
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.docstore.document import Document as LangchainDocument

from app.core.config import settings
from app.core.schemas import ComplianceStatus, ComplianceIssue, VerificationResponse
from app.utils.rag_utils import clean_and_fix_json

logger = logging.getLogger(__name__)

class ComplianceService:
    """Service for verifying prompt compliance with policies."""
    
    def __init__(self):
        """Initialize the compliance service."""
        self.policies_dir = settings.policies_dir
        self.db_dir = settings.policies_db_dir
        self.vector_store = None
        self.llm = None
        self.embeddings = None
        self.qa_chain = None
        
        # Initialize the system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the system components."""
        try:
            logger.info("Initializing compliance verification system...")
            
            # Create directories if they don't exist
            os.makedirs(self.policies_dir, exist_ok=True)
            os.makedirs(self.db_dir, exist_ok=True)
            os.makedirs("temp", exist_ok=True)
            
            # Initialize the embedding model
            self._initialize_embeddings()
            
            # Initialize the LLM
            self._initialize_llm()
            
            # Initialize or load the vector store
            self._initialize_vector_store()
            
            # Initialize the QA chain for retrieval
            self._initialize_qa_chain()
            
            logger.info("System initialization complete.")
            
        except Exception as e:
            logger.error(f"Error initializing system: {str(e)}")
            raise
    
    def _initialize_embeddings(self):
        """Initialize the embedding model."""
        try:
            # Using Azure OpenAI for embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_type="azure",
                deployment=settings.azure_openai_embedding_deployment,
                openai_api_version=settings.azure_openai_api_version,
                openai_api_key=settings.azure_openai_api_key,
                openai_api_base=settings.azure_openai_endpoint,
            )
            logger.info("Embedding model initialized.")
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise
    
    def _initialize_llm(self):
        """Initialize the language model."""
        try:
            # Using Azure OpenAI for the LLM
            self.llm = AzureChatOpenAI(
                deployment_name=settings.azure_openai_deployment,
                openai_api_version=settings.azure_openai_api_version,
                openai_api_key=settings.azure_openai_api_key,
                openai_api_base=settings.azure_openai_endpoint,
                temperature=0.0  # Use zero temperature for more deterministic responses
            )
            logger.info("Language model initialized.")
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
    
    def _initialize_vector_store(self):
        """Initialize or load the vector store with policy documents."""
        try:
            # Check if vector store already exists
            if os.path.exists(self.db_dir) and os.listdir(self.db_dir):
                # Load existing vector store
                logger.info("Loading existing vector store...")
                self.vector_store = Chroma(
                    persist_directory=self.db_dir,
                    embedding_function=self.embeddings
                )
                logger.info(f"Loaded vector store from {self.db_dir}")
            else:
                # Create new vector store from policy documents
                logger.info("Creating new vector store from policy documents...")
                self._create_vector_store()
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise
    
    def _create_vector_store(self):
        """Create a new vector store from policy documents."""
        try:
            # Check if there are policy documents
            policy_files = [f for f in os.listdir(self.policies_dir) 
                           if os.path.isfile(os.path.join(self.policies_dir, f)) 
                           and f.endswith(('.txt', '.md', '.json'))]
            
            if not policy_files:
                logger.warning(f"No policy documents found in {self.policies_dir}")
                # Create an empty vector store
                self.vector_store = Chroma(
                    persist_directory=self.db_dir,
                    embedding_function=self.embeddings
                )
                return
            
            # Load documents
            documents = []
            for file in policy_files:
                try:
                    loader = TextLoader(os.path.join(self.policies_dir, file))
                    docs = loader.load()
                    documents.extend(docs)
                except Exception as e:
                    logger.error(f"Error loading document {file}: {str(e)}")
            
            if not documents:
                logger.warning("No documents could be loaded.")
                self.vector_store = Chroma(
                    persist_directory=self.db_dir,
                    embedding_function=self.embeddings
                )
                return
            
            logger.info(f"Loaded {len(documents)} policy documents.")
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)
            logger.info(f"Split into {len(splits)} chunks.")
            
            # Create vector store
            self.vector_store = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory=self.db_dir
            )
            
            # Persist the vector store
            self.vector_store.persist()
            logger.info(f"Created and persisted vector store with {len(splits)} chunks.")
            
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    def _initialize_qa_chain(self):
        """Initialize the QA chain for retrieval."""
        try:
            # Create a prompt template for compliance verification
            template = """
            You are a compliance verification expert. Your task is to determine if the user's prompt
            complies with the company's policies and regulations.
            
            Review the following policies that are relevant to the user's prompt:
            {context}
            
            User Prompt:
            {question}
            
            Assess if the user's prompt complies with the above policies. In your assessment:
            1. Identify any specific conflicts between the prompt and the policies
            2. Explain why each identified part conflicts with a specific policy
            3. Rate the severity of each issue on a scale of 1-10
            4. Provide an overall compliance score from 0-10 (where 10 is fully compliant)
            
            Format your response as a JSON object with the following structure:
            {{
                "status": "COMPLIANT", "NON_COMPLIANT", or "UNCERTAIN",
                "compliance_score": A number from 0 to 10,
                "issues": [
                    {{
                        "policy_text": "The specific policy text that is relevant",
                        "prompt_text": "The part of the prompt that conflicts with the policy",
                        "severity": A number from 1 to 10,
                        "explanation": "A clear explanation of the conflict"
                    }}
                ],
                "relevant_policies": ["Policy 1", "Policy 2", ...]
            }}
            
            If the prompt complies with all policies, return a "COMPLIANT" status, a high compliance score,
            and an empty issues array.
            
            IMPORTANT: Only return the valid JSON object with no additional text, markdown formatting,
            or code block markers.
            """
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["context", "question"]
            )
            
            # Create the QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}  # Retrieve top 5 most relevant chunks
                ),
                chain_type_kwargs={"prompt": prompt}
            )
            
            logger.info("QA chain initialized.")
            
        except Exception as e:
            logger.error(f"Error initializing QA chain: {str(e)}")
            raise
    
    def add_policy_document(self, document_path: str) -> bool:
        """
        Add a new policy document to the vector store.
        
        Args:
            document_path: Path to the document file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Adding policy document: {document_path}")
            
            # Ensure the document exists
            if not os.path.exists(document_path):
                logger.error(f"Document does not exist: {document_path}")
                return False
            
            # Load the document
            loader = TextLoader(document_path)
            documents = loader.load()
            
            # Split document into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)
            
            # Add to vector store
            self.vector_store.add_documents(splits)
            
            # Persist the vector store
            self.vector_store.persist()
            
            logger.info(f"Successfully added document with {len(splits)} chunks.")
            return True
            
        except Exception as e:
            logger.error(f"Error adding policy document: {str(e)}")
            return False
    
    def add_policy_text(self, policy_text: str, policy_name: Optional[str] = None) -> bool:
        """
        Add policy text directly to the vector store.
        
        Args:
            policy_text: The policy text to add
            policy_name: Optional name for the policy
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if policy_name is None:
                policy_name = f"policy_{uuid.uuid4().hex[:8]}"
                
            logger.info(f"Adding policy text: {policy_name}")
            
            # Create a document
            document = LangchainDocument(
                page_content=policy_text,
                metadata={"source": policy_name}
            )
            
            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents([document])
            
            # Add to vector store
            self.vector_store.add_documents(splits)
            
            # Persist the vector store
            self.vector_store.persist()
            
            # Also save to a file for reference
            policy_file_path = os.path.join(self.policies_dir, f"{policy_name}.txt")
            with open(policy_file_path, "w", encoding="utf-8") as file:
                file.write(policy_text)
            
            logger.info(f"Successfully added policy text with {len(splits)} chunks.")
            return True
            
        except Exception as e:
            logger.error(f"Error adding policy text: {str(e)}")
            return False
    
    def list_policies(self) -> List[str]:
        """
        List all policy documents.
        
        Returns:
            List of policy document names
        """
        try:
            policy_files = [f for f in os.listdir(self.policies_dir) 
                           if os.path.isfile(os.path.join(self.policies_dir, f)) 
                           and f.endswith(('.txt', '.md', '.json'))]
            return policy_files
        except Exception as e:
            logger.error(f"Error listing policies: {str(e)}")
            return []
    
    def clear_policies(self) -> bool:
        """
        Clear all policies from the system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete vector store
            if self.vector_store:
                self.vector_store = None
            
            # Delete all files in the db directory
            if os.path.exists(self.db_dir):
                shutil.rmtree(self.db_dir)
                os.makedirs(self.db_dir, exist_ok=True)
            
            # Delete policy files but keep the directory
            policy_files = [f for f in os.listdir(self.policies_dir) 
                           if os.path.isfile(os.path.join(self.policies_dir, f)) 
                           and f.endswith(('.txt', '.md', '.json'))]
            
            for file in policy_files:
                os.remove(os.path.join(self.policies_dir, file))
            
            # Reinitialize the vector store
            self._initialize_vector_store()
            
            # Reinitialize the QA chain
            self._initialize_qa_chain()
            
            logger.info("Successfully cleared all policies.")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing policies: {str(e)}")
            return False
    
    async def verify_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Verify if a prompt complies with the policies.
        
        Args:
            prompt: The user prompt to verify
            
        Returns:
            Verification result dictionary
        """
        try:
            logger.info("Verifying prompt compliance...")
            
            # Check if there are any policies
            if self.vector_store._collection.count() == 0:
                logger.warning("No policies found in vector store.")
                return VerificationResponse(
                    status=ComplianceStatus.UNCERTAIN,
                    compliance_score=5.0,
                    issues=[
                        ComplianceIssue(
                            policy_text="No policies have been defined.",
                            prompt_text=prompt,
                            severity=5.0,
                            explanation="Cannot verify compliance as no policies have been defined."
                        )
                    ],
                    relevant_policies=[]
                ).dict()
            
            # Query the QA chain
            response = self.qa_chain({"query": prompt})
            raw_result = response.get("result", "{}")
            
            # Parse the JSON response
            try:
                # Clean and fix the JSON response
                result_json = clean_and_fix_json(raw_result)
                
                # Create ComplianceIssue objects
                issues = []
                for issue_data in result_json.get("issues", []):
                    issues.append(ComplianceIssue(
                        policy_text=issue_data.get("policy_text", ""),
                        prompt_text=issue_data.get("prompt_text", ""),
                        severity=float(issue_data.get("severity", 5.0)),
                        explanation=issue_data.get("explanation", "")
                    ))
                
                # Create and return the result
                return VerificationResponse(
                    status=ComplianceStatus(result_json.get("status", "UNCERTAIN")),
                    compliance_score=float(result_json.get("compliance_score", 5.0)),
                    issues=issues,
                    relevant_policies=result_json.get("relevant_policies", [])
                ).dict()
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {raw_result}")
                logger.error(f"JSON parse error: {str(e)}")
                
                # Return an uncertain result
                return VerificationResponse(
                    status=ComplianceStatus.UNCERTAIN,
                    compliance_score=5.0,
                    issues=[
                        ComplianceIssue(
                            policy_text="",
                            prompt_text=prompt,
                            severity=5.0,
                            explanation=f"Failed to parse compliance analysis: {str(e)}"
                        )
                    ],
                    relevant_policies=[]
                ).dict()
                
        except Exception as e:
            logger.error(f"Error verifying prompt: {str(e)}")
            
            # Return an error result
            return VerificationResponse(
                status=ComplianceStatus.UNCERTAIN,
                compliance_score=0.0,
                issues=[
                    ComplianceIssue(
                        policy_text="",
                        prompt_text=prompt,
                        severity=10.0,
                        explanation=f"Error during compliance verification: {str(e)}"
                    )
                ],
                relevant_policies=[]
            ).dict()