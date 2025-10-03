"""
Test script for schema context builder
Verifies schema introspection works correctly
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent.schema_context import SchemaContextBuilder


def test_basic_introspection():
    """Test basic database introspection"""
    print("\nTest 1: Basic Introspection")
    print("-" * 70)
    
    builder = SchemaContextBuilder()
    tables = builder.get_all_tables()
    
    expected_tables = {'drivers', 'vehicles', 'maintenance_records', 
                      'telemetry', 'driver_performance', 'fault_codes'}
    found_tables = {table.name for table in tables}
    
    if expected_tables == found_tables:
        print("✓ All expected tables found")
    else:
        print("✗ Missing tables:", expected_tables - found_tables)
        return False
    
    for table in tables:
        print(f"  - {table.name}: {table.row_count:,} rows, {len(table.columns)} columns")
    
    return True


def test_column_details():
    """Test column introspection"""
    print("\nTest 2: Column Details")
    print("-" * 70)
    
    builder = SchemaContextBuilder()
    vehicles = builder.get_table_info('vehicles')
    
    # Check for key columns
    column_names = [col.name for col in vehicles.columns]
    expected_columns = ['id', 'make', 'model', 'vin', 'license_plate', 
                       'current_mileage', 'next_service_due']
    
    missing = [col for col in expected_columns if col not in column_names]
    if missing:
        print(f"✗ Missing columns: {missing}")
        return False
    
    print("✓ All expected columns found")
    
    # Check for primary key
    pk_cols = [col.name for col in vehicles.columns if col.primary_key]
    if 'id' in pk_cols:
        print(f"✓ Primary key detected: {pk_cols}")
    else:
        print("✗ Primary key not detected")
        return False
    
    # Check for foreign keys
    fk_cols = [(col.name, col.foreign_key) for col in vehicles.columns if col.foreign_key]
    print(f"  Foreign keys found: {len(fk_cols)}")
    
    return True


def test_relationships():
    """Test foreign key relationship detection"""
    print("\nTest 3: Relationship Detection")
    print("-" * 70)
    
    builder = SchemaContextBuilder()
    
    # Check telemetry foreign keys
    telemetry = builder.get_table_info('telemetry')
    fks = {col.name: col.foreign_key for col in telemetry.columns if col.foreign_key}
    
    if 'vehicle_id' in fks and 'vehicles.id' in fks['vehicle_id']:
        print("✓ vehicle_id -> vehicles.id detected")
    else:
        print("✗ vehicle_id foreign key not detected correctly")
        return False
    
    if 'driver_id' in fks and 'drivers.id' in fks['driver_id']:
        print("✓ driver_id -> drivers.id detected")
    else:
        print("✗ driver_id foreign key not detected correctly")
        return False
    
    print(f"  Total foreign keys in telemetry: {len(fks)}")
    return True


def test_full_context():
    """Test full context generation"""
    print("\nTest 4: Full Context Generation")
    print("-" * 70)
    
    builder = SchemaContextBuilder()
    context = builder.build_schema_context()
    
    # Check for key sections
    required_sections = [
        "FleetFix Database Schema",
        "Tables Overview",
        "Detailed Schema",
        "Key Relationships",
        "Important Notes"
    ]
    
    missing_sections = [sec for sec in required_sections if sec not in context]
    if missing_sections:
        print(f"✗ Missing sections: {missing_sections}")
        return False
    
    print("✓ All required sections present")
    print(f"  Total context length: {len(context):,} characters")
    print(f"  Approximate tokens: ~{len(context) // 4:,}")
    
    # Show first few lines
    lines = context.split('\n')
    print("\n  First 10 lines:")
    for line in lines[:10]:
        print(f"    {line}")
    
    return True


def test_concise_context():
    """Test concise context generation"""
    print("\nTest 5: Concise Context Generation")
    print("-" * 70)
    
    builder = SchemaContextBuilder()
    concise = builder.build_concise_context()
    full = builder.build_schema_context()
    
    reduction = (1 - len(concise) / len(full)) * 100
    print(f"✓ Concise context generated")
    print(f"  Full context: {len(full):,} chars")
    print(f"  Concise context: {len(concise):,} chars")
    print(f"  Reduction: {reduction:.1f}%")
    
    # Show concise output
    print("\n  Concise context preview:")
    for line in concise.split('\n')[:15]:
        print(f"    {line}")
    
    return True


def test_sample_data():
    """Test sample data retrieval"""
    print("\nTest 6: Sample Data Retrieval")
    print("-" * 70)
    
    builder = SchemaContextBuilder()
    
    # Get samples from each table
    tables = ['drivers', 'vehicles', 'fault_codes']
    
    for table in tables:
        samples = builder.get_table_sample_data(table, limit=1)
        if samples and 'error' not in samples[0]:
            print(f"✓ {table}: Sample retrieved successfully")
            # Show a few fields
            sample = samples[0]
            fields = list(sample.keys())[:3]
            preview = {k: sample[k] for k in fields}
            print(f"    Preview: {preview}")
        else:
            print(f"✗ {table}: Failed to retrieve sample")
            return False
    
    return True


def test_token_estimation():
    """Test and display token usage estimates"""
    print("\nTest 7: Token Usage Estimation")
    print("-" * 70)
    
    builder = SchemaContextBuilder()
    
    full_context = builder.build_schema_context()
    concise_context = builder.build_concise_context()
    
    # Rough token estimation (1 token ≈ 4 characters for English text)
    full_tokens = len(full_context) // 4
    concise_tokens = len(concise_context) // 4
    
    print(f"  Full context: ~{full_tokens:,} tokens")
    print(f"  Concise context: ~{concise_tokens:,} tokens")
    print(f"\n  Recommendation:")
    if full_tokens < 2000:
        print("    Use full context (plenty of room in LLM context window)")
    else:
        print("    Consider concise context for token efficiency")
    
    return True


def save_contexts_to_files():
    """Save both context versions to files for inspection"""
    print("\nSaving contexts to files...")
    print("-" * 70)
    
    builder = SchemaContextBuilder()
    
    # Save full context
    full_path = "schema_context_full.txt"
    with open(full_path, 'w') as f:
        f.write(builder.build_schema_context())
    print(f"✓ Full context saved to: {full_path}")
    
    # Save concise context
    concise_path = "schema_context_concise.txt"
    with open(concise_path, 'w') as f:
        f.write(builder.build_concise_context())
    print(f"✓ Concise context saved to: {concise_path}")
    
    print("\nYou can inspect these files to see what gets sent to the LLM!")


def main():
    """Run all tests"""
    print("=" * 70)
    print("Schema Context Builder - Test Suite")
    print("=" * 70)
    
    tests = [
        ("Basic Introspection", test_basic_introspection),
        ("Column Details", test_column_details),
        ("Relationship Detection", test_relationships),
        ("Full Context", test_full_context),
        ("Concise Context", test_concise_context),
        ("Sample Data", test_sample_data),
        ("Token Estimation", test_token_estimation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Save context files
    try:
        save_contexts_to_files()
    except Exception as e:
        print(f"✗ Failed to save context files: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Schema context builder is ready.")
        print("\nNext steps:")
        print("  1. Review schema_context_full.txt to see what LLM receives")
        print("  2. Move to text-to-SQL implementation")
        print("  3. Test with example queries")
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review errors above.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
