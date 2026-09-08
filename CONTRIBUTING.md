# Contributing to SomaOS

Thank you for your interest in contributing to SomaOS robot brain projects!

## Ways to Contribute

- **Bug reports**: Open an issue with the bug label, include reproduction steps
- **Feature requests**: Open an issue with the enhancement label, describe the use case
- **Documentation**: Fix typos, add examples, improve clarity
- **Code**: Submit PRs for bug fixes or features

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit with clear messages: `git commit -m "feat: add X for Y"`
4. Push and open a PR against `main`
5. Ensure CI passes (sync-to-gitee workflow)

## Code Style

- Python: Follow PEP 8, use type hints, semantic naming
- JavaScript: ES6+, async/await over callbacks
- YAML: 2-space indent

## Safety Considerations

This is a robotics project. Any changes affecting:
- Safety gating or emergency stop logic
- Motor control or kinematics
- Sim-to-real transfer

...require extra review. Tag such PRs with the `safety-critical` label.

## License

By contributing, you agree your contributions are licensed under Apache-2.0.
