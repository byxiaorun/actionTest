#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os, sys
import requests

class GitActionCleaner():

    def __init__(self):
        self.envInfo = {
            'GITHUB_REPOSITORY': '当前仓库的路径 "用户名/仓库名", action中已经预设',
            'GITHUB_WORKFLOW': '当前 workflow 名字, action中已经预设',
            'GIT_API_TOKEN': 'GitHub API token, action中可以使用 ${{ github.token }} 获取,也可自行申请',
            'recordSavedNum': '删除交老的记录时保留多少个, 默认10个'
        }

    def initArgs(self):
        # GitHub API Token
        self.gitToken = os.environ['GIT_API_TOKEN']
        # 保留的记录数量 默认10
        savedNum = os.environ['recordSavedNum'] if ('recordSavedNum' in os.environ) else 10
        self.savedNum = int(savedNum) - 1
        # 当前 workflow run 的名字
        self.wfName = os.environ['GITHUB_WORKFLOW']
        # 当前 action 的 '用户名/仓库名' 如 inused/actionTest
        self.gitRepo = os.environ['GITHUB_REPOSITORY']
        # API 地址
        self.gitApi = f'https://api.github.com/repos/{self.gitRepo}/actions/runs'
        # GitHub API 请求头 Accept
        self.headerAccept = 'application/vnd.github.v3+json'
        # 请求头
        self.header = {'Accept': self.headerAccept, 'Authorization': f'token {self.gitToken}'}
        self.httpSession = requests.session()
        self.httpSession.headers.update(self.header)

    def main(self):
        try:
            self.initArgs()
        except KeyError as e:
            self.help()
            e = str(e).strip("'")
            print(f'\n需要设置环境变量 {e}: {self.envInfo[e]}')
            sys.exit(0)
        # 获取所有运行记录
        self.getAllRuns()
        # 删除已取消
        self.delRun(self.getCancelledIds())
        # 删除早期的
        self.delRun(self.getOldIds())

    def getCancelledIds(self):
        """删除所有取消状态的 workflow run 记录"""
        cancelledIds = []
        l = len(self.runs) - 1
        for i in range(l, -1, -1):
            run = self.runs[i]
            if run['conclusion'] == 'cancelled':
                # 提取id
                cancelledIds.append(run['id'])
                # 从列表中删除
                self.runs.remove(run)
        print('删除已经取消的记录:', cancelledIds)
        return cancelledIds

    def getOldIds(self):
        """删除指定name的workflow早期的 run 记录"""
        oldIds = []
        for run in self.runs:
            if run['name'] == self.wfName:
                oldIds.append(run['id'])
        oldIds = oldIds[self.savedNum:]
        print('删除比较老的记录:', oldIds)
        return oldIds

    def delRun(self, runIds):
        """通过id删除运行记录"""
        for runId in runIds:
            res = self.httpSession.delete(f"{self.gitApi}/{runId}")
            print(res.headers)
            print(res.text)

    def getAllRuns(self):
        """获取当前仓库action的所有运行记录 分页最大一次获取100条"""
        runs = self.httpSession.get(f"{self.gitApi}?per_page=100")
        self.runs = runs.json()['workflow_runs']

    def help(self):
        print('\n1.删除当前仓库里所有cancelled状态的run.')
        print('2.删除当前workflow比较老的run(默认保存最新的10个run记录).')
        print('* 需要设置环境变量以下环境变量:')
        print(f'  * GITHUB_REPOSITORY: {self.envInfo["GITHUB_REPOSITORY"]}')
        print(f'  * GITHUB_WORKFLOW: {self.envInfo["GITHUB_WORKFLOW"]}')
        print(f'  * GIT_API_TOKEN: {self.envInfo["GIT_API_TOKEN"]}')
        print(f'  * recordSavedNum: {self.envInfo["recordSavedNum"]}\n')

if __name__ == '__main__':
    a = GitActionCleaner().main()
