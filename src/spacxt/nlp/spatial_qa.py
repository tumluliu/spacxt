"""
Spatial Context Q&A System for SpacXT - enables intelligent space-aware question answering.

This system leverages the rich spatial context representation to answer complex spatial queries
about object relationships, dependencies, and spatial reasoning.
"""

from typing import Dict, List, Any, Optional, Tuple
from ..core.graph_store import SceneGraph, Node, Relation
from ..physics.support_system import SupportSystem
from ..physics.collision_detector import CollisionDetector
from .llm_client import LLMClient


class SpatialContextAnalyzer:
    """Analyzes and extracts rich spatial context from the scene graph."""

    def __init__(self, scene_graph: SceneGraph, support_system: SupportSystem):
        self.graph = scene_graph
        self.support_system = support_system

    def get_comprehensive_spatial_context(self) -> Dict[str, Any]:
        """Generate comprehensive spatial context for Q&A."""

        # Basic scene information
        objects = {}
        for obj_id, node in self.graph.nodes.items():
            objects[obj_id] = {
                "id": obj_id,
                "class": node.cls,
                "position": node.pos,
                "size": node.bbox['xyz'],
                "affordances": node.aff,
                "level_of_mobility": node.lom,
                "state": node.state,
                "confidence": node.conf
            }

        # Spatial relationships with confidence scores
        relationships = []
        for (rel_type, a, b), relation in self.graph.relations.items():
            relationships.append({
                "type": rel_type,
                "subject": a,
                "object": b,
                "properties": relation.props,
                "confidence": relation.conf,
                "timestamp": relation.ts
            })

        # Support dependencies
        support_info = self.support_system.get_system_status()

        # Spatial clusters and regions
        spatial_clusters = self._analyze_spatial_clusters()

        # Accessibility analysis
        accessibility = self._analyze_accessibility()

        # Stability analysis
        stability = self._analyze_stability()

        return {
            "scene_summary": {
                "total_objects": len(objects),
                "object_types": list(set(node.cls for node in self.graph.nodes.values())),
                "relationship_types": list(set(rel[0] for rel in self.graph.relations.keys())),
                "scene_bounds": self._calculate_scene_bounds()
            },
            "objects": objects,
            "relationships": relationships,
            "support_dependencies": support_info,
            "spatial_clusters": spatial_clusters,
            "accessibility": accessibility,
            "stability": stability,
            "spatial_reasoning": self._generate_spatial_insights()
        }

    def _analyze_spatial_clusters(self) -> List[Dict[str, Any]]:
        """Identify spatial clusters and regions in the scene."""
        clusters = []

        # Simple clustering based on proximity
        processed = set()
        for obj_id, node in self.graph.nodes.items():
            if obj_id in processed:
                continue

            cluster = {
                "center_object": obj_id,
                "objects": [obj_id],
                "center_position": node.pos,
                "cluster_type": "singleton"
            }

            # Find nearby objects
            neighbors = self.graph.neighbors(obj_id, radius=1.0)
            for neighbor in neighbors:
                if neighbor.id not in processed:
                    cluster["objects"].append(neighbor.id)
                    processed.add(neighbor.id)

            # Classify cluster type
            if len(cluster["objects"]) > 1:
                # Determine cluster characteristics
                object_classes = [self.graph.nodes[oid].cls for oid in cluster["objects"]]
                if "table" in object_classes:
                    cluster["cluster_type"] = "table_group"
                elif "stove" in object_classes:
                    cluster["cluster_type"] = "cooking_area"
                else:
                    cluster["cluster_type"] = "object_group"

            processed.add(obj_id)
            clusters.append(cluster)

        return clusters

    def _analyze_accessibility(self) -> Dict[str, Any]:
        """Analyze object accessibility and reachability."""
        accessibility = {
            "reachable_objects": [],
            "blocked_objects": [],
            "accessibility_scores": {}
        }

        for obj_id, node in self.graph.nodes.items():
            # Simple accessibility based on mobility and support
            score = 1.0

            # Reduce score if object is supported by another
            supporting_obj = self.support_system.support_tracker.get_supporting_object(obj_id)
            if supporting_obj:
                score *= 0.8  # Slightly less accessible if on something

            # Reduce score based on level of mobility
            if node.lom == "fixed":
                score *= 0.2
            elif node.lom == "low":
                score *= 0.6

            accessibility["accessibility_scores"][obj_id] = score

            if score > 0.7:
                accessibility["reachable_objects"].append(obj_id)
            elif score < 0.3:
                accessibility["blocked_objects"].append(obj_id)

        return accessibility

    def _analyze_stability(self) -> Dict[str, Any]:
        """Analyze structural stability of the scene."""
        stability = {
            "stable_structures": [],
            "unstable_objects": [],
            "support_chains": []
        }

        # Analyze support chains
        for supporter_id, dependents in self.support_system.support_tracker.dependents.items():
            if dependents:
                chain = {
                    "base": supporter_id,
                    "supported_objects": list(dependents),
                    "chain_length": len(dependents),
                    "stability_risk": "low" if len(dependents) <= 2 else "medium"
                }
                stability["support_chains"].append(chain)

                if len(dependents) > 3:
                    stability["unstable_objects"].extend(list(dependents))

        # Find stable base objects (not supported by anything)
        for obj_id in self.graph.nodes.keys():
            if not self.support_system.support_tracker.get_supporting_object(obj_id):
                stability["stable_structures"].append(obj_id)

        return stability

    def _calculate_scene_bounds(self) -> Dict[str, Tuple[float, float]]:
        """Calculate the spatial bounds of the scene."""
        if not self.graph.nodes:
            return {"x": (0, 0), "y": (0, 0), "z": (0, 0)}

        positions = [node.pos for node in self.graph.nodes.values()]
        sizes = [node.bbox['xyz'] for node in self.graph.nodes.values()]

        min_x = min(pos[0] - size[0]/2 for pos, size in zip(positions, sizes))
        max_x = max(pos[0] + size[0]/2 for pos, size in zip(positions, sizes))
        min_y = min(pos[1] - size[1]/2 for pos, size in zip(positions, sizes))
        max_y = max(pos[1] + size[1]/2 for pos, size in zip(positions, sizes))
        min_z = min(pos[2] - size[2]/2 for pos, size in zip(positions, sizes))
        max_z = max(pos[2] + size[2]/2 for pos, size in zip(positions, sizes))

        return {
            "x": (min_x, max_x),
            "y": (min_y, max_y),
            "z": (min_z, max_z)
        }

    def _generate_spatial_insights(self) -> List[str]:
        """Generate high-level spatial insights about the scene."""
        insights = []

        # Count relationships by type
        rel_counts = {}
        for (rel_type, _, _) in self.graph.relations.keys():
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1

        # Generate insights based on relationships
        if rel_counts.get("on_top_of", 0) > 0:
            insights.append(f"Scene has {rel_counts['on_top_of']} stacking relationships")

        if rel_counts.get("supports", 0) > 0:
            insights.append(f"Scene has {rel_counts['supports']} support structures")

        # Support dependency insights
        support_info = self.support_system.get_system_status()
        if support_info["scene_analysis"]["supported_objects"] > 0:
            insights.append(f"{support_info['scene_analysis']['supported_objects']} objects depend on others for support")

        # Mobility insights
        fixed_objects = [obj for obj in self.graph.nodes.values() if obj.lom == "fixed"]
        if fixed_objects:
            insights.append(f"{len(fixed_objects)} objects are fixed in place")

        return insights


class SpatialQASystem:
    """Intelligent spatial question-answering system."""

    def __init__(self, scene_graph: SceneGraph, support_system: SupportSystem):
        self.analyzer = SpatialContextAnalyzer(scene_graph, support_system)
        self.graph = scene_graph
        self.support_system = support_system

        # Initialize LLM client for advanced reasoning
        try:
            self.llm_client = LLMClient()
            self.llm_available = True
        except Exception:
            self.llm_available = False

    def answer_spatial_question(self, question: str) -> Dict[str, Any]:
        """Answer a spatial question using the rich spatial context."""

        # Get comprehensive spatial context
        spatial_context = self.analyzer.get_comprehensive_spatial_context()

        # Classify question type
        question_type = self._classify_question(question)

        # Generate answer based on question type
        if question_type == "relationship":
            answer = self._answer_relationship_question(question, spatial_context)
        elif question_type == "location":
            answer = self._answer_location_question(question, spatial_context)
        elif question_type == "accessibility":
            answer = self._answer_accessibility_question(question, spatial_context)
        elif question_type == "stability":
            answer = self._answer_stability_question(question, spatial_context)
        elif question_type == "what_if":
            answer = self._answer_what_if_question(question, spatial_context)
        elif question_type == "complex":
            answer = self._answer_complex_question(question, spatial_context)
        else:
            answer = self._answer_general_question(question, spatial_context)

        return {
            "question": question,
            "question_type": question_type,
            "answer": answer,
            "confidence": answer.get("confidence", 0.8),
            "spatial_context_used": spatial_context["scene_summary"]
        }

    def _classify_question(self, question: str) -> str:
        """Classify the type of spatial question."""
        question_lower = question.lower()

        # Relationship questions
        if any(word in question_lower for word in ["relationship", "related", "connected", "on", "near", "beside", "support"]):
            return "relationship"

        # Location questions
        elif any(word in question_lower for word in ["where", "location", "position", "find", "locate"]):
            return "location"

        # Accessibility questions
        elif any(word in question_lower for word in ["reach", "access", "get", "move", "blocked"]):
            return "accessibility"

        # Stability questions
        elif any(word in question_lower for word in ["stable", "fall", "collapse", "support", "depends"]):
            return "stability"

        # What-if questions
        elif any(word in question_lower for word in ["what if", "if i", "happen", "remove", "move"]):
            return "what_if"

        # Complex reasoning questions
        elif any(word in question_lower for word in ["why", "how", "explain", "reason"]):
            return "complex"

        else:
            return "general"

    def _answer_relationship_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Answer questions about spatial relationships."""

        relationships = context["relationships"]
        objects = context["objects"]

        # Extract object names from question
        mentioned_objects = []
        for obj_id in objects.keys():
            if obj_id.lower() in question.lower() or objects[obj_id]["class"] in question.lower():
                mentioned_objects.append(obj_id)

        relevant_relationships = []
        for rel in relationships:
            if rel["subject"] in mentioned_objects or rel["object"] in mentioned_objects:
                relevant_relationships.append(rel)

        if relevant_relationships:
            answer_text = "Found these spatial relationships:\n"
            for rel in relevant_relationships:
                subj_class = objects[rel["subject"]]["class"]
                obj_class = objects[rel["object"]]["class"]
                answer_text += f"• {rel['subject']} ({subj_class}) {rel['type']} {rel['object']} ({obj_class}) [confidence: {rel['confidence']:.2f}]\n"
        else:
            answer_text = "No specific spatial relationships found for the mentioned objects."

        return {
            "answer_text": answer_text,
            "relationships": relevant_relationships,
            "confidence": 0.9 if relevant_relationships else 0.6
        }

    def _answer_location_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Answer questions about object locations."""

        objects = context["objects"]
        clusters = context["spatial_clusters"]

        # Find mentioned objects
        mentioned_objects = []
        for obj_id, obj_data in objects.items():
            if obj_id.lower() in question.lower() or obj_data["class"] in question.lower():
                mentioned_objects.append((obj_id, obj_data))

        if mentioned_objects:
            answer_text = "Object locations:\n"
            for obj_id, obj_data in mentioned_objects:
                pos = obj_data["position"]
                answer_text += f"• {obj_id} ({obj_data['class']}) is at position ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})\n"

                # Add cluster information
                for cluster in clusters:
                    if obj_id in cluster["objects"]:
                        answer_text += f"  - Part of {cluster['cluster_type']} with {len(cluster['objects'])} objects\n"
                        break
        else:
            answer_text = "Could not identify specific objects in your question."

        return {
            "answer_text": answer_text,
            "located_objects": mentioned_objects,
            "confidence": 0.9 if mentioned_objects else 0.4
        }

    def _answer_accessibility_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Answer questions about object accessibility."""

        accessibility = context["accessibility"]
        objects = context["objects"]

        answer_text = "Accessibility analysis:\n"

        if "reachable" in question.lower() or "reach" in question.lower():
            reachable = accessibility["reachable_objects"]
            answer_text += f"• {len(reachable)} objects are easily reachable:\n"
            for obj_id in reachable[:5]:  # Show first 5
                obj_class = objects[obj_id]["class"]
                score = accessibility["accessibility_scores"][obj_id]
                answer_text += f"  - {obj_id} ({obj_class}) [accessibility: {score:.2f}]\n"

        if "blocked" in question.lower():
            blocked = accessibility["blocked_objects"]
            if blocked:
                answer_text += f"• {len(blocked)} objects have limited accessibility:\n"
                for obj_id in blocked:
                    obj_class = objects[obj_id]["class"]
                    score = accessibility["accessibility_scores"][obj_id]
                    answer_text += f"  - {obj_id} ({obj_class}) [accessibility: {score:.2f}]\n"
            else:
                answer_text += "• No objects are currently blocked\n"

        return {
            "answer_text": answer_text,
            "accessibility_data": accessibility,
            "confidence": 0.8
        }

    def _answer_stability_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Answer questions about structural stability."""

        stability = context["stability"]
        support_deps = context["support_dependencies"]

        answer_text = "Stability analysis:\n"

        if stability["support_chains"]:
            answer_text += f"• Found {len(stability['support_chains'])} support structures:\n"
            for chain in stability["support_chains"]:
                base_obj = chain["base"]
                supported_count = len(chain["supported_objects"])
                risk = chain["stability_risk"]
                answer_text += f"  - {base_obj} supports {supported_count} objects [risk: {risk}]\n"

        if stability["unstable_objects"]:
            answer_text += f"• {len(stability['unstable_objects'])} objects may be unstable:\n"
            for obj_id in stability["unstable_objects"][:3]:  # Show first 3
                answer_text += f"  - {obj_id}\n"

        stable_count = len(stability["stable_structures"])
        answer_text += f"• {stable_count} objects are stable base structures\n"

        return {
            "answer_text": answer_text,
            "stability_data": stability,
            "confidence": 0.85
        }

    def _answer_what_if_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Answer hypothetical 'what if' questions."""

        support_deps = context["support_dependencies"]
        objects = context["objects"]

        answer_text = "Hypothetical analysis:\n"

        # Look for removal scenarios
        if "remove" in question.lower():
            # Try to identify which object would be removed
            for obj_id, obj_data in objects.items():
                if obj_id.lower() in question.lower() or obj_data["class"] in question.lower():
                    # Check what depends on this object
                    dependents = support_deps.get("dependents", {}).get(obj_id, [])
                    if dependents:
                        answer_text += f"If {obj_id} is removed:\n"
                        answer_text += f"• {len(dependents)} objects would fall due to gravity:\n"
                        for dep_id in dependents:
                            dep_class = objects[dep_id]["class"]
                            answer_text += f"  - {dep_id} ({dep_class})\n"
                    else:
                        answer_text += f"If {obj_id} is removed:\n• No other objects would be affected\n"
                    break

        return {
            "answer_text": answer_text,
            "confidence": 0.7
        }

    def _answer_complex_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Answer complex reasoning questions using LLM if available."""

        if self.llm_available:
            return self._answer_with_llm(question, context)
        else:
            return {
                "answer_text": "Complex reasoning requires LLM capabilities. Please set up OpenRouter API key.",
                "confidence": 0.3
            }

    def _answer_with_llm(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM for advanced spatial reasoning."""

        # Build comprehensive context for LLM
        context_str = f"""
Scene Summary: {context['scene_summary']}

Objects in scene:
{chr(10).join([f"- {obj_id}: {obj_data['class']} at {obj_data['position']}" for obj_id, obj_data in context['objects'].items()])}

Spatial Relationships:
{chr(10).join([f"- {rel['subject']} {rel['type']} {rel['object']} (conf: {rel['confidence']:.2f})" for rel in context['relationships']])}

Support Dependencies:
{chr(10).join([f"- {supporter} supports: {', '.join(dependents)}" for supporter, dependents in context['support_dependencies'].get('dependents', {}).items()])}

Spatial Insights:
{chr(10).join([f"- {insight}" for insight in context['spatial_reasoning']])}
"""

        system_prompt = f"""You are a spatial reasoning expert analyzing a 3D scene.

Current scene context:
{context_str}

Answer the user's spatial question with detailed reasoning based on the spatial context provided.
Consider object positions, relationships, support dependencies, and physical constraints.
Provide specific, actionable insights based on the spatial data.
"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.3,
                max_tokens=800
            )

            answer_text = response.choices[0].message.content.strip()

            return {
                "answer_text": answer_text,
                "reasoning_type": "llm_enhanced",
                "confidence": 0.9
            }

        except Exception as e:
            return {
                "answer_text": f"Error in LLM reasoning: {str(e)}",
                "confidence": 0.2
            }

    def _answer_general_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Answer general questions about the scene."""

        scene_summary = context["scene_summary"]
        spatial_insights = context["spatial_reasoning"]

        answer_text = f"""Scene Overview:
• Total objects: {scene_summary['total_objects']}
• Object types: {', '.join(scene_summary['object_types'])}
• Relationship types: {', '.join(scene_summary['relationship_types'])}
• Scene bounds: X({scene_summary['scene_bounds']['x'][0]:.1f}, {scene_summary['scene_bounds']['x'][1]:.1f}), Y({scene_summary['scene_bounds']['y'][0]:.1f}, {scene_summary['scene_bounds']['y'][1]:.1f}), Z({scene_summary['scene_bounds']['z'][0]:.1f}, {scene_summary['scene_bounds']['z'][1]:.1f})

Key Insights:
{chr(10).join([f'• {insight}' for insight in spatial_insights])}
"""

        return {
            "answer_text": answer_text,
            "scene_overview": scene_summary,
            "confidence": 0.8
        }
