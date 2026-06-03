import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs/promises';

// Loads .github/instructions/*.instructions.md whose `applyTo` globs match the
// target file, and concatenates their bodies into the cacheable system context.
// This wires the extension to the SAME instruction library as the bashos CLI and
// every other agent surface (AGENTS.md), so Claude edits to house style here
// obey the same rules as everywhere else.

const INSTRUCTIONS_DIR = '.github/instructions';

/** Tiny, dependency-free glob → RegExp (supports `**\/`, `**`, `*`, `?`). */
function globToRegExp(glob: string): RegExp {
    // 1) escape regex specials (leave * and ? for wildcard expansion)
    // 2) swap wildcards for sentinels so later passes don't rewrite earlier output
    // 3) expand sentinels to their regex equivalents
    const body = glob
        .replace(/[.+^${}()|[\]\\]/g, '\\$&')
        .replace(/\*\*\//g, '@@GLOBSTAR_SLASH@@')
        .replace(/\*\*/g, '@@GLOBSTAR@@')
        .replace(/\*/g, '[^/]*')
        .replace(/\?/g, '[^/]')
        .replace(/@@GLOBSTAR_SLASH@@/g, '(?:.*/)?')
        .replace(/@@GLOBSTAR@@/g, '.*');
    return new RegExp('^' + body + '$');
}

function matchesApplyTo(relPath: string, applyTo: string): boolean {
    return applyTo
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
        .some((pattern) => globToRegExp(pattern).test(relPath));
}

function stripFrontmatter(text: string): { applyTo: string; body: string } {
    const m = text.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    if (!m) {
        return { applyTo: '', body: text };
    }
    const fm = m[1];
    const applyToMatch = fm.match(/^applyTo:\s*["']?(.+?)["']?\s*$/m);
    return { applyTo: applyToMatch ? applyToMatch[1] : '', body: m[2].trim() };
}

/**
 * Returns the concatenated instruction bodies whose `applyTo` matches the file,
 * or an empty string if none match / the directory is absent.
 */
export async function loadInstructionContext(
    workspaceRoot: string,
    fileUri: vscode.Uri,
    output: vscode.OutputChannel,
): Promise<string> {
    const dir = path.join(workspaceRoot, INSTRUCTIONS_DIR);
    const relPath = path.relative(workspaceRoot, fileUri.fsPath).split(path.sep).join('/');

    let files: string[];
    try {
        files = (await fs.readdir(dir)).filter((f) => f.endsWith('.instructions.md'));
    } catch {
        return '';
    }

    const parts: string[] = [];
    for (const file of files) {
        try {
            const text = await fs.readFile(path.join(dir, file), 'utf-8');
            const { applyTo, body } = stripFrontmatter(text);
            if (applyTo && matchesApplyTo(relPath, applyTo)) {
                parts.push(`<!-- ${file} -->\n${body}`);
            }
        } catch (error) {
            output.appendLine(`[instructions] skipped ${file}: ${error}`);
        }
    }
    return parts.join('\n\n---\n\n');
}
