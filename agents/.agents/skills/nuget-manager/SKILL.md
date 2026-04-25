---
name: nuget-manager
description: 'Manage NuGet packages in .NET projects/solutions. Use this skill when adding, removing, or updating NuGet package versions. It enforces using `dotnet` CLI for package management and provides strict procedures for direct file edits only when updating versions.'
---

# NuGet Manager

Use this skill to manage NuGet package operations safely via the dotnet CLI.

## Rules

- Use `dotnet add package` for add operations.
- Use `dotnet remove package` for remove operations.
- Direct file edits are only for version updates.
- Validate with `dotnet restore` after version changes.

## Reference

Source skill in repository: `.github/skills/nuget-manager/SKILL.md`.
