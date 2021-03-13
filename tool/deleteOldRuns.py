#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import sys
import json
import requests
from argparse import ArgumentParser


class GitActionCleaner():
    def __init__(self):
        # 当前脚本真实路径
        self.curPath = os.path.realpath(__file__)
        # 当前脚本所在文件夹
        self.curDir = os.path.dirname(self.curPath)
        # 当前脚本文件名
        self.curName = os.path.basename(self.curPath)
        # GitHub API Token
        self.gitToken = os.environ['GIT_API_TOKEN']
        # 保留的记录数量 默认10
        self.savedNum = os.environ['recordSavedNum'] if ('recordSavedNum' in os.environ) else 10
        # 当前 workflow run 的名字
        self.wfName = os.environ['GITHUB_WORKFLOW']
        # 当前 action 的 '用户名/仓库名' 如 inused/actionTest
        self.gitRepo = os.environ['GITHUB_REPOSITORY']
        # API 地址
        self.gitApi = f'https://api.github.com/repos/{self.args.gitRepo}/actions/runs'
        # GitHub API 请求头 Accept
        self.headerAccept = 'application/vnd.github.v3+json'
        # 请求头
        self.header = {'Accept': self.headerAccept, 'Authorization': f'token {self.gitToken}'}
        self.httpSession = requests.session()
        self.httpSession.headers.update(self.header)

    def main(self):
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
        print('删除比较老的记录:', oldIds)
        return oldIds[self.savedNum:]

    def delRun(self, runIds):
        """通过id删除运行记录"""
        for runId in runIds:
            res = self.httpSession.delete(f"{self.gitApi}/{runId}")
            print(res.text)

    def getAllRuns(self):
        """获取当前仓库action的所有运行记录 分页最大一次获取100条"""
        runs = self.httpSession.get(f"{self.gitApi}?per_page=100")
        self.runs = runs.json()['workflow_runs']

if __name__ == '__main__':
    try:
        GitActionCleaner().main()
    except KeyError as e:
        print(f'\n需要设置环境变量 {e},或者给出对应的参数')