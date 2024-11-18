# Anthropic-Autogen Framework Refactor Plan

This document outlines the step-by-step plan to refactor our framework to better align with Autogen's design patterns and implementation.

## 1. Runtime System Migration

### Phase 1: Remove Custom Runtime Implementation
- [x] Remove custom runtime classes:
  - `/src/anthropic_autogen/core/runtime.py`
  - `/src/anthropic_autogen/core/runtime_v2.py`
  - `/src/anthropic_autogen/runtimes/single_threaded.py`
- [x] Update Orchestrator to use autogen-core runtimes directly:
  - Default to `SingleThreadedAgentRuntime`
  - Support `WorkerAgentRuntime` for distributed scenarios
  - Remove custom Runtime dependency

### Phase 2: Memory System Integration
- [ ] Keep our custom memory system as an enhancement layer
- [ ] Create memory-aware agent base class:
  ```python
  class MemoryAwareAgent(RoutedAgent):  # from autogen_core.base
      def __init__(self, memory_store: Optional[BaseMemoryStore] = None):
          self.memory = memory_store or InMemoryStore()
  ```
- [ ] Create memory provider for runtime integration:
  ```python
  class MemoryProvider:
      def get_agent_memory(self, agent_id: str) -> BaseMemoryStore:
          return AgentMemoryView(self.store, agent_id)
  ```

### Phase 3: Agent Updates
- [ ] Update existing agents to work with new runtime system
- [ ] Add memory capabilities through MemoryAwareAgent base class
- [ ] Ensure proper message routing and task delegation
- [ ] Update tests to use autogen-core runtimes

### Phase 4: Documentation & Examples
- [ ] Update documentation to reflect new runtime architecture
- [ ] Create examples showing:
  - Basic agent setup with autogen-core runtime
  - Memory system integration
  - Distributed runtime usage
- [ ] Document migration path for existing users

## 2. Message System Alignment

### 2.1 Message Types
- [ ] Review and align message types with Autogen's system
- [ ] Remove redundant message types
- [ ] Ensure proper inheritance from Autogen base types
- [ ] Add memory-aware message types

### 2.2 Message Handling
- [ ] Update message routing to use autogen-core runtime
- [ ] Add memory integration for message history
- [ ] Implement proper error handling
- [ ] Add support for message metadata

## 3. Agent System Enhancement

### 3.1 Base Agent Implementation
- [ ] Update base agent to use autogen-core runtime
- [ ] Add memory capabilities to base agent
- [ ] Implement proper message handling
- [ ] Add telemetry support

### 3.2 Specialized Agents
- [ ] Update specialized agents to use new base
- [ ] Add memory-aware features
- [ ] Implement proper tool handling
- [ ] Add support for agent-specific memory types

## 4. Tool System Updates

### 4.1 Tool Integration
- [ ] Update tool system to work with autogen-core
- [ ] Add memory integration for tool results
- [ ] Implement proper error handling
- [ ] Add telemetry support

### 4.2 Memory-Aware Tools
- [ ] Add memory capabilities to tools
- [ ] Implement tool result caching
- [ ] Add support for tool-specific memory types

## 5. Testing and Documentation

### 5.1 Test Updates
- [ ] Update test suite for new architecture
- [ ] Add memory system tests
- [ ] Add integration tests
- [ ] Update test utilities

### 5.2 Documentation
- [ ] Update architecture documentation
- [ ] Add memory system documentation
- [ ] Update API documentation
- [ ] Add migration guide

## Memory System Enhancements

Our memory system remains a key differentiator with unique features:
- Semantic vector search with embeddings
- Structured memory entries
- Async implementation with proper locking
- Metadata-rich memory management
- Agent-specific memory tracking
- Similarity-based search with configurable thresholds

### Integration Strategy
1. Use autogen-core's runtime directly
2. Add our memory system as an optional enhancement
3. Provide memory mixins/decorators for agents
4. Maintain backward compatibility

## Dependencies
- autogen-core (0.4.0.dev6)
- openai (for embeddings)
- scikit-learn (for vector search)
- numpy
- opentelemetry

## Security Considerations
- Maintain proper access controls in memory system
- Implement robust error handling
- Ensure type safety in async methods
- Protect sensitive information in memory entries

## Testing Strategy
1. Unit tests for runtime integration
2. Integration tests for memory system
3. Performance benchmarks
4. Security testing
5. Backward compatibility tests

## Benefits of New Architecture

1. Better alignment with autogen-core:
   - Direct use of proven runtime implementations
   - Proper message routing and handling
   - Standard agent lifecycle management

2. Enhanced memory capabilities:
   - Vector-based semantic search
   - Structured memory entries
   - Agent-specific memory types
   - Memory-aware message handling

3. Improved maintainability:
   - Less custom code to maintain
   - Better separation of concerns
   - Clearer integration points

4. Future-proof design:
   - Easy to adopt autogen-core updates
   - Extensible memory system
   - Clear upgrade paths

## Phase 1: Runtime System Migration 
- [x] Remove custom runtime classes
- [x] Update Orchestrator to use autogen-core runtimes directly
- [x] Clean up runtime-related imports

## Phase 2: Memory System Refactoring 

### 2.1 Mixin Reorganization
- [ ] Split RuntimeMixin into:
  - `MemoryMixin`: Core memory capabilities
  - `ConversationMixin`: Conversation features with memory integration
- [ ] Update mixin interfaces to be more focused and cohesive
- [ ] Add proper type hints and documentation

### 2.2 Agent Hierarchy Update
- [ ] Make memory capabilities optional in base agents
- [ ] Create new agent hierarchy:
  ```
  BaseAgent (no memory)
  ├── MemoryAgent (memory capabilities)
  └── ConversationalAgent (conversation + memory)
  
  BaseToolAgent (no memory)
  ├── MemoryToolAgent (memory capabilities)
  └── ConversationalToolAgent (conversation + memory)
  ```
- [ ] Update existing agents to use appropriate base classes
- [ ] Add migration guide for users

### 2.3 Memory System Enhancements
- [ ] Keep vector-based semantic search
- [ ] Maintain async-first design
- [ ] Ensure proper memory isolation between agents
- [ ] Add memory type system for better organization

## Phase 3: Integration & Testing

### 3.1 Core Integration
- [ ] Update message handling with memory integration
- [ ] Add conversation history tracking
- [ ] Implement task memory tracking
- [ ] Add memory search capabilities

### 3.2 Testing Strategy
- [ ] Unit tests for memory mixins
- [ ] Integration tests for agent memory
- [ ] Conversation tracking tests
- [ ] Performance benchmarks
- [ ] Memory isolation tests

## Key Features

### Memory System
- Semantic vector search with embeddings
- Structured memory entries
- Async implementation with proper locking
- Metadata-rich memory management
- Agent-specific memory tracking
- Similarity-based search with configurable thresholds

### Agent Capabilities
- Optional memory integration
- Flexible conversation tracking
- Task history tracking
- Semantic search across memories
- Memory isolation between agents

## Dependencies
- autogen-core (0.4.0.dev6)
- openai (for embeddings)
- scikit-learn (for vector search)
- numpy
- opentelemetry

## Security & Performance
- Memory access controls
- Proper async locking
- Efficient vector search
- Memory cleanup on agent termination
