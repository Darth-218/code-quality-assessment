"""
Module for extracting comprehensive software metrics taxonomy.
"""

import json
from typing import Dict, List, Any

def extract_metrics_taxonomy() -> Dict[str, Any]:
    """
    Extract and organize the complete software metrics taxonomy.
    
    Returns:
        Dictionary containing the organized metrics taxonomy
    """
    
    taxonomy = {
        "I. Object-Oriented (OO) and Core Product Metrics": get_oo_metrics(),
        "II. General Static Source Code Metrics": get_general_metrics(),
        "III. Change and Process Metrics": get_change_metrics(),
        "IV. Technical Debt (TD) and Refactoring Features": get_td_metrics(),
        "V. Graph and Structural Features": get_graph_features(),
        "VI. Semantic and Textual Features": get_semantic_features(),
        "VII. Target Variables and Derived Scores": get_target_variables()
    }
    
    return taxonomy

def get_oo_metrics() -> List[Dict[str, Any]]:
    """Extract Object-Oriented metrics (CK suite and related)."""
    return [
        {
            "metric_name": "DIT",
            "full_name": "Depth of Inheritance Tree",
            "category": "OO Metric (Inheritance)",
            "description": "Maximum inheritance path from the class to the root class",
            "formula": "DIT = max(depth from class to root)",
            "measurement_level": "Class",
            "typical_range": "0-10+",
            "optimal_value": "Low to moderate (1-3)",
            "citations": ["Chidamber & Kemerer, 1994"],
            "interpretation": "Higher values may indicate increased complexity and fragility",
            "tools": ["CKJM", "Understand", "SonarQube", "PMD"]
        },
        {
            "metric_name": "LCOM",
            "full_name": "Lack of Cohesion in Methods",
            "category": "OO Metric (Cohesion)",
            "description": "Measures the dissimilarity of methods in a class by instance variable usage",
            "variants": ["LCOM1", "LCOM2", "LCOM3", "LCOM4", "LCOM5"],
            "measurement_level": "Class",
            "typical_range": "0-∞",
            "optimal_value": "Low (closer to 0)",
            "citations": ["Chidamber & Kemerer, 1994"],
            "interpretation": "Higher values indicate poor cohesion; values > 1 suggest refactoring needed",
            "tools": ["CKJM", "Understand"]
        },
        {
            "metric_name": "NOC",
            "full_name": "Number of Children",
            "category": "OO Metric (Inheritance)",
            "description": "Number of immediate subclasses of a class",
            "measurement_level": "Class",
            "typical_range": "0-∞",
            "optimal_value": "Moderate",
            "citations": ["Chidamber & Kemerer, 1994"],
            "interpretation": "High NOC may indicate over-specialization",
            "tools": ["CKJM", "Understand"]
        },
        {
            "metric_name": "RFC",
            "full_name": "Response For a Class",
            "category": "OO Metric (Coupling)",
            "description": "Number of methods that can be executed in response to a message to the object",
            "measurement_level": "Class",
            "typical_range": "1-100+",
            "optimal_value": "Lower is better",
            "citations": ["Chidamber & Kemerer, 1994"],
            "interpretation": "High RFC indicates complex classes with many responsibilities",
            "tools": ["CKJM", "Understand"]
        },
        {
            "metric_name": "WMC",
            "full_name": "Weighted Methods per Class",
            "category": "OO Metric (Complexity)",
            "description": "Sum of complexities of all methods in a class",
            "measurement_level": "Class",
            "typical_range": "1-100+",
            "optimal_value": "Lower is better",
            "citations": ["Chidamber & Kemerer, 1994"],
            "interpretation": "High WMC indicates complex classes",
            "tools": ["CKJM", "Understand"]
        },
        {
            "metric_name": "CBO",
            "full_name": "Coupling Between Object classes",
            "category": "OO Metric (Coupling)",
            "description": "Count of classes to which a given class is coupled",
            "measurement_level": "Class",
            "typical_range": "0-∞",
            "optimal_value": "Low (0-10)",
            "citations": ["Chidamber & Kemerer, 1994"],
            "interpretation": "Lower values preferred; high CBO reduces reusability",
            "tools": ["CKJM", "Understand", "SonarQube"]
        },
        {
            "metric_name": "NOM",
            "full_name": "Number of Methods",
            "category": "OO Metric (Encapsulation)",
            "description": "Total number of methods in a class",
            "measurement_level": "Class",
            "typical_range": "1-100+",
            "optimal_value": "Moderate (5-20)",
            "interpretation": "Very high NOM may indicate God Class anti-pattern",
            "tools": ["CKJM", "Understand"]
        }
    ]

def get_general_metrics() -> Dict[str, List[Dict[str, Any]]]:
    """Extract General Static Source Code Metrics organized by subcategory."""
    return {
        "A. Size Metrics": [
            {
                "metric_name": "LOC",
                "full_name": "Lines of Code",
                "description": "Total lines of code including blanks and comments",
                "variants": ["SLOC", "LLOC", "CLOC", "TLOC"],
                "measurement_level": ["Method", "Class", "File", "Package"],
                "typical_range": "Method: 1-50, Class: 10-500",
                "usage": "Basic size indicator, often used as normalization factor",
                "tools": ["cloc", "radon", "SonarQube"]
            },
            {
                "metric_name": "LLOC",
                "full_name": "Logical Lines of Code",
                "description": "Count of executable statements",
                "measurement_level": ["Method", "Class", "File"],
                "typical_range": "Method: 1-30, Class: 5-300",
                "interpretation": "More accurate than LOC for complexity assessment",
                "tools": ["radon", "pylint"]
            },
            {
                "metric_name": "NCL",
                "full_name": "Number of Classes",
                "description": "Count of classes in a module or package",
                "measurement_level": ["Package", "System"],
                "interpretation": "System complexity indicator",
                "tools": ["pydeps", "structure101"]
            }
        ],
        
        "B. Complexity Metrics": [
            {
                "metric_name": "McCC",
                "full_name": "McCabe's Cyclomatic Complexity",
                "description": "Measures the number of linearly independent paths through a program",
                "formula": "M = E - N + 2P (E=edges, N=nodes, P=connected components)",
                "measurement_level": ["Method"],
                "thresholds": {
                    "simple": "1-10",
                    "moderate": "11-20", 
                    "complex": "21-40",
                    "untestable": ">40"
                },
                "recommendation": "Keep methods below 15 for maintainability",
                "tools": ["radon", "mccabe", "SonarQube"]
            },
            {
                "metric_name": "NL",
                "full_name": "Nesting Level",
                "description": "Maximum depth of control structure nesting",
                "measurement_level": ["Method"],
                "optimal_value": "≤ 4",
                "interpretation": "High nesting indicates complex control flow",
                "tools": ["radon", "pylint"]
            }
        ],
        
        "C. Coupling Metrics": [
            {
                "metric_name": "Ca",
                "full_name": "Afferent Coupling",
                "description": "Number of classes that depend on this class",
                "relationship": "Incoming dependencies",
                "interpretation": "High Ca indicates responsibility and stability",
                "tools": ["JDepend", "Structure101"]
            },
            {
                "metric_name": "Ce", 
                "full_name": "Efferent Coupling",
                "description": "Number of classes this class depends on",
                "relationship": "Outgoing dependencies",
                "interpretation": "High Ce indicates fragility and instability",
                "tools": ["JDepend", "Structure101"]
            }
        ],
        
        "D. Inheritance Metrics": [
            {
                "metric_name": "NOA",
                "full_name": "Number of Ancestors",
                "description": "Count of superclasses in the inheritance chain",
                "relation_to_DIT": "NOA = DIT (in some definitions)",
                "interpretation": "Deep inheritance hierarchies can be problematic",
                "tools": ["CKJM", "Understand"]
            }
        ],
        
        "E. Documentation Metrics": [
            {
                "metric_name": "CD",
                "full_name": "Comment Density",
                "description": "Ratio of comment lines to total lines of code",
                "formula": "CD = CLOC / (CLOC + SLOC)",
                "measurement_level": ["Method", "Class", "File"],
                "recommended_range": "20-40%",
                "interpretation": "Too low: poor documentation; Too high: possibly commented-out code",
                "tools": ["radon", "pydocstyle"]
            },
            {
                "metric_name": "CLOC",
                "full_name": "Comment Lines of Code",
                "description": "Number of lines containing comments",
                "measurement_level": ["Method", "Class", "File"],
                "interpretation": "Indicates documentation effort",
                "tools": ["cloc", "radon"]
            }
        ],
        
        "F. Other General Metrics": [
            {
                "metric_name": "Halstead_Volume",
                "category": "Halstead Metrics",
                "description": "Measures the size of the implementation of an algorithm",
                "formula": "V = N × log₂(n) where N = total operators+operands, n = unique operators+operands",
                "sub_metrics": [
                    "n1: Number of distinct operators",
                    "n2: Number of distinct operands", 
                    "N1: Total number of operators",
                    "N2: Total number of operands",
                    "Vocabulary (n): n1 + n2",
                    "Length (N): N1 + N2",
                    "Volume (V): N × log₂(n)",
                    "Difficulty (D): (n1/2) × (N2/n2)",
                    "Effort (E): D × V"
                ],
                "tools": ["radon", "halstead"]
            }
        ]
    }

def get_change_metrics() -> List[Dict[str, Any]]:
    """Extract Change and Process Metrics."""
    return [
        {
            "metric_name": "CC",
            "full_name": "Change Count",
            "description": "Number of times a component has been modified",
            "data_source": "Version Control System (e.g., Git)",
            "measurement_level": ["File", "Class", "Method"],
            "interpretation": "Frequently changed components may be unstable or error-prone",
            "calculation": "git log --oneline <file> | wc -l"
        },
        {
            "metric_name": "NR",
            "full_name": "Number of Revisions",
            "description": "Total number of revisions/commits for a component",
            "data_source": "Version Control System",
            "interpretation": "Indicates evolution and maintenance activity",
            "tools": ["git", "svn", "hg"]
        },
        {
            "metric_name": "NDC",
            "full_name": "Number of Distinct Committers",
            "description": "Count of unique developers who modified a component",
            "data_source": "Version Control System",
            "interpretation": "High NDC may indicate knowledge diffusion or lack of ownership",
            "calculation": "git log --format='%aN' <file> | sort -u | wc -l"
        }
    ]

def get_td_metrics() -> List[Dict[str, Any]]:
    """Extract Technical Debt and Refactoring Features."""
    return [
        {
            "feature_name": "TD_Severity",
            "description": "Severity level of technical debt issues",
            "levels": [
                {"name": "INFO", "value": 1, "description": "Minor issue, cosmetic"},
                {"name": "MINOR", "value": 2, "description": "Small issue, low impact"},
                {"name": "MAJOR", "value": 3, "description": "Important issue, should be fixed"},
                {"name": "CRITICAL", "value": 4, "description": "Critical issue, high impact"},
                {"name": "BLOCKER", "value": 5, "description": "Blocking issue, must be fixed immediately"}
            ],
            "common_source": "SonarQube, Checkstyle, PMD, ESLint"
        },
        {
            "feature_name": "TD_Type",
            "description": "Type of technical debt issue",
            "categories": [
                {"name": "CODE_SMELL", "value": 1, "description": "Maintainability issue"},
                {"name": "BUG", "value": 2, "description": "Reliability issue, potential defect"},
                {"name": "VULNERABILITY", "value": 3, "description": "Security issue"}
            ],
            "common_source": "SonarQube"
        }
    ]

def get_graph_features() -> List[Dict[str, Any]]:
    """Extract Graph and Structural Features."""
    return [
        {
            "feature_name": "Adjacency_Matrix_A",
            "description": "Matrix representing class dependencies in the system",
            "representation": "A[i][j] = 1 if class i depends on class j, 0 otherwise",
            "dimensionality": "n × n where n = number of classes",
            "usage": "Graph neural network input for system-level analysis",
            "extraction_tools": ["jdeprscan", "dependency-cruiser"]
        },
        {
            "feature_name": "Node_Feature_Vector_X",
            "description": "Feature vector for each class node in the dependency graph",
            "typical_dimensions": "20-30 features per node",
            "content": "Combination of class-level metrics (e.g., WMC, DIT, CBO, NOM, RFC, LCOM, etc.)",
            "usage": "Node features in Graph Neural Networks"
        }
    ]

def get_semantic_features() -> List[Dict[str, Any]]:
    """Extract Semantic and Textual Features."""
    return [
        {
            "feature_name": "Defect_Summary_Embedding",
            "description": "Vector representation of defect summary text",
            "extraction_methods": ["TF-IDF", "Word2Vec", "FastText", "BERT", "RoBERTa", "CodeBERT"],
            "typical_dimensionality": "TF-IDF: 100-5000, BERT: 768",
            "application": "Defect classification, duplicate detection"
        },
        {
            "feature_name": "BERTopic_Clusters",
            "description": "Topic modeling features from defect descriptions using BERTopic",
            "application": "Automatic categorization of defect root causes",
            "typical_topics": ["Test Data issues", "Environment issues", "Design issues", "Configuration issues"]
        }
    ]

def get_target_variables() -> List[Dict[str, Any]]:
    """Extract Target Variables and Derived Scores."""
    return [
        {
            "target_name": "Bug_Count",
            "type": "Regression target (Continuous)",
            "description": "Number of defects in a module/class",
            "data_source": "Bug tracking systems (JIRA, Bugzilla, GitHub Issues)",
            "prediction_task": "Defect prediction",
            "evaluation_metrics": ["MSE", "MAE", "R²"]
        },
        {
            "target_name": "Defect_Density",
            "type": "Regression target (Continuous)",
            "description": "Number of defects per thousand lines of code",
            "formula": "DD = (Bug_Count / KLOC) × 1000",
            "typical_range": "0-50 defects/KLOC",
            "industry_benchmark": "1-25 defects/KLOC (varies by domain)"
        },
        {
            "target_name": "Maintainability_Index",
            "type": "Composite score (Continuous)",
            "description": "Composite metric of maintainability (based on Halstead, McCabe, LOC)",
            "formula": "MI = 171 - 5.2 × ln(Halstead_Volume) - 0.23 × (Cyclomatic_Complexity) - 16.2 × ln(LOC)",
            "scale": "0-100 (higher is better)",
            "interpretation": {
                "85-100": "Highly maintainable",
                "65-85": "Moderately maintainable", 
                "0-65": "Difficult to maintain"
            }
        },
        {
            "target_name": "Maintainability_Status",
            "type": "Classification target (Categorical)",
            "categories": ["Excellent", "Good", "Fair", "Poor", "Very Poor"],
            "mapping": "Usually derived from Maintainability Index thresholds"
        }
    ]