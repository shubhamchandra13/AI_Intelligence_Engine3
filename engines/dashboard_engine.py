def print_index_dashboard(index, data):

    print("\n" + "=" * 60)
    print(f"📊 INDEX: {index}")
    print("-" * 60)

    structure = data["structure"]
    liquidity = data["liquidity"]
    confidence = data["confidence"]

    print("STRUCTURE")
    print(f"  Bias: {structure['bias']}")
    print(f"  Structure: {structure['structure']}")
    print(f"  BOS: {structure['bos']}")
    print(f"  CHOCH: {structure['choch']}")

    print("\nSMART MONEY")
    print(f"  Liquidity: {liquidity['status']} ({liquidity['strength']})")

    print("\nPERFORMANCE")
    print(f"  Confidence: {confidence['confidence']}%")
    print(f"  Grade: {confidence['grade']}")