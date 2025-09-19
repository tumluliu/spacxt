#!/usr/bin/env python3
"""
Spatial Context & Q&A Demo for SpacXT

This demo showcases the comprehensive spatial context representation and
intelligent question-answering capabilities of the SpacXT system.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from spacxt import SceneGraph, Bus, make_agents
from spacxt.nlp.spatial_qa import SpatialQASystem, SpatialContextAnalyzer
from spacxt.nlp.scene_modifier import SceneModifier
from spacxt.physics.support_system import SupportSystem
import json


def load_demo_scene():
    """Load a more complex demo scene for Q&A demonstration."""

    # Load the basic bootstrap scene
    with open('bootstrap.json', 'r') as f:
        data = json.load(f)

    scene_graph = SceneGraph()
    scene_graph.load_bootstrap(data)

    # Add more objects to create a richer scene
    from spacxt.core.graph_store import Node, GraphPatch

    # Add cups on the table
    cup1 = Node(
        id="coffee_cup_1",
        cls="cup",
        pos=(1.3, 1.5, 1.15),  # On table
        ori=(0, 0, 0, 1),
        bbox={"type": "OBB", "xyz": [0.08, 0.08, 0.10]},
        aff=["hold_liquid", "portable"],
        lom="high",
        conf=0.95
    )

    cup2 = Node(
        id="coffee_cup_2",
        cls="cup",
        pos=(1.7, 1.5, 1.15),  # On table
        ori=(0, 0, 0, 1),
        bbox={"type": "OBB", "xyz": [0.08, 0.08, 0.10]},
        aff=["hold_liquid", "portable"],
        lom="high",
        conf=0.95
    )

    # Add a book on the table
    book = Node(
        id="book_1",
        cls="book",
        pos=(1.5, 1.2, 1.14),  # On table
        ori=(0, 0, 0, 1),
        bbox={"type": "OBB", "xyz": [0.15, 0.23, 0.03]},
        aff=["readable", "portable"],
        lom="high",
        conf=0.96
    )

    # Add a lamp near the stove
    lamp = Node(
        id="lamp_1",
        cls="lamp",
        pos=(3.8, 1.2, 0.25),  # On ground near stove
        ori=(0, 0, 0, 1),
        bbox={"type": "OBB", "xyz": [0.15, 0.15, 0.50]},
        aff=["illuminate"],
        lom="low",
        conf=0.90
    )

    # Apply patch to add objects
    patch = GraphPatch()
    patch.add_nodes["coffee_cup_1"] = cup1
    patch.add_nodes["coffee_cup_2"] = cup2
    patch.add_nodes["book_1"] = book
    patch.add_nodes["lamp_1"] = lamp
    scene_graph.apply_patch(patch)

    return scene_graph


def demonstrate_spatial_context():
    """Demonstrate the comprehensive spatial context representation."""

    print("=" * 60)
    print("🌟 SPATIAL CONTEXT REPRESENTATION DEMO")
    print("=" * 60)

    # Load demo scene
    scene_graph = load_demo_scene()
    bus = Bus()
    agents = make_agents(scene_graph, bus, list(scene_graph.nodes.keys()))

    # Create systems
    scene_modifier = SceneModifier(scene_graph, bus, agents)
    support_system = scene_modifier.support_system
    spatial_analyzer = SpatialContextAnalyzer(scene_graph, support_system)

    # Analyze support relationships
    support_system.analyze_and_update_support_relationships()

    # Get comprehensive spatial context
    spatial_context = spatial_analyzer.get_comprehensive_spatial_context()

    print("\n📊 SCENE SUMMARY:")
    summary = spatial_context["scene_summary"]
    print(f"• Total objects: {summary['total_objects']}")
    print(f"• Object types: {', '.join(summary['object_types'])}")
    print(f"• Relationship types: {', '.join(summary['relationship_types'])}")
    print(f"• Scene bounds: X({summary['scene_bounds']['x'][0]:.1f}, {summary['scene_bounds']['x'][1]:.1f}) "
          f"Y({summary['scene_bounds']['y'][0]:.1f}, {summary['scene_bounds']['y'][1]:.1f}) "
          f"Z({summary['scene_bounds']['z'][0]:.1f}, {summary['scene_bounds']['z'][1]:.1f})")

    print("\n🎯 OBJECTS IN SCENE:")
    for obj_id, obj_data in spatial_context["objects"].items():
        pos = obj_data["position"]
        print(f"• {obj_id} ({obj_data['class']}) at ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
        print(f"  - Size: {obj_data['size']}")
        print(f"  - Mobility: {obj_data['level_of_mobility']}")
        if obj_data["affordances"]:
            print(f"  - Affordances: {', '.join(obj_data['affordances'])}")

    print("\n🔗 SPATIAL RELATIONSHIPS:")
    for rel in spatial_context["relationships"]:
        print(f"• {rel['subject']} {rel['type']} {rel['object']} (confidence: {rel['confidence']:.2f})")
        if rel["properties"]:
            print(f"  - Properties: {rel['properties']}")

    print("\n🏗️ SUPPORT DEPENDENCIES:")
    support_deps = spatial_context["support_dependencies"]
    scene_analysis = support_deps["scene_analysis"]
    print(f"• Ground objects: {scene_analysis['ground_objects']}")
    print(f"• Supported objects: {scene_analysis['supported_objects']}")
    print(f"• Floating objects: {scene_analysis['floating_objects']}")

    if support_deps["dependents"]:
        print("• Support relationships:")
        for supporter, dependents in support_deps["dependents"].items():
            print(f"  - {supporter} supports: {', '.join(dependents)}")

    print("\n🎪 SPATIAL CLUSTERS:")
    for cluster in spatial_context["spatial_clusters"]:
        print(f"• {cluster['cluster_type']}: {', '.join(cluster['objects'])}")
        print(f"  - Center: {cluster['center_object']}")

    print("\n🚪 ACCESSIBILITY ANALYSIS:")
    accessibility = spatial_context["accessibility"]
    print(f"• Reachable objects: {', '.join(accessibility['reachable_objects'])}")
    if accessibility["blocked_objects"]:
        print(f"• Blocked objects: {', '.join(accessibility['blocked_objects'])}")

    print("\n⚖️ STABILITY ANALYSIS:")
    stability = spatial_context["stability"]
    print(f"• Stable base structures: {len(stability['stable_structures'])}")
    if stability["support_chains"]:
        print(f"• Support chains: {len(stability['support_chains'])}")
        for chain in stability["support_chains"]:
            print(f"  - {chain['base']} → {len(chain['supported_objects'])} objects (risk: {chain['stability_risk']})")

    print("\n🧠 SPATIAL INSIGHTS:")
    for insight in spatial_context["spatial_reasoning"]:
        print(f"• {insight}")

    return scene_graph, support_system


def demonstrate_spatial_qa():
    """Demonstrate intelligent spatial question answering."""

    print("\n" + "=" * 60)
    print("🤔 SPATIAL Q&A SYSTEM DEMO")
    print("=" * 60)

    # Get scene from previous demo
    scene_graph, support_system = demonstrate_spatial_context()

    # Create Q&A system
    qa_system = SpatialQASystem(scene_graph, support_system)

    # Demo questions covering different categories
    demo_questions = [
        # Relationship questions
        "What objects are on the table?",
        "What is the relationship between the cups and the table?",

        # Location questions
        "Where is the lamp located?",
        "Where are all the cups in the scene?",

        # Accessibility questions
        "Which objects can I easily reach?",
        "Are any objects blocked or hard to access?",

        # Stability questions
        "What objects would fall if I remove the table?",
        "Which objects are stable and which depend on others?",

        # What-if questions
        "What if I remove the table?",
        "What would happen if the chair is moved?",

        # Complex questions (requires LLM if available)
        "Why are the cups positioned where they are?",
        "How would you reorganize this scene for better accessibility?",

        # General questions
        "Tell me about the overall scene layout",
        "What are the main spatial features of this kitchen?"
    ]

    print("\n🎯 ANSWERING SPATIAL QUESTIONS:")
    print("-" * 40)

    for i, question in enumerate(demo_questions, 1):
        print(f"\n{i}. Q: {question}")

        try:
            # Get answer from Q&A system
            qa_result = qa_system.answer_spatial_question(question)

            # Display results
            print(f"   Type: {qa_result['question_type']}")
            print(f"   Confidence: {qa_result['confidence']:.1%}")
            print(f"   A: {qa_result['answer']['answer_text']}")

            if i % 3 == 0:  # Add separator every 3 questions
                print("-" * 40)

        except Exception as e:
            print(f"   Error: {str(e)}")

    print("\n✨ Q&A DEMO COMPLETE!")

    return qa_system


def main():
    """Run the complete spatial context and Q&A demonstration."""

    print("🚀 SpacXT Spatial Context & Q&A System")
    print("Demonstrating advanced spatial reasoning capabilities\n")

    try:
        # Run both demonstrations
        demonstrate_spatial_context()
        qa_system = demonstrate_spatial_qa()

        print("\n" + "=" * 60)
        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("\nKey Capabilities Demonstrated:")
        print("✅ Comprehensive spatial context representation")
        print("✅ Multi-layered relationship detection")
        print("✅ Support dependency tracking")
        print("✅ Spatial clustering and region analysis")
        print("✅ Accessibility and stability analysis")
        print("✅ Intelligent question classification")
        print("✅ Context-aware answer generation")
        print("✅ Multi-modal spatial reasoning")

        print(f"\n📊 Scene Statistics:")
        context = qa_system.analyzer.get_comprehensive_spatial_context()
        summary = context["scene_summary"]
        print(f"• Objects: {summary['total_objects']}")
        print(f"• Relationships: {len(context['relationships'])}")
        print(f"• Support chains: {len(context['stability']['support_chains'])}")
        print(f"• Spatial clusters: {len(context['spatial_clusters'])}")

        print("\n💡 This spatial context enables:")
        print("• Space-aware question answering")
        print("• Predictive 'what-if' scenarios")
        print("• Accessibility and safety analysis")
        print("• Intelligent scene understanding")
        print("• Context-driven decision making")

    except Exception as e:
        print(f"❌ Demo error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
